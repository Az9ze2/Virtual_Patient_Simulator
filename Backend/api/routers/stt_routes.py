"""
Enhanced Speech-to-Text (STT) Routes with Medical Terminology Correction
Uses OpenAI Whisper API + GPT-4 mini for Thai medical conversations
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from fastapi.responses import JSONResponse
import openai
import os
from typing import Dict, Any, Optional
import tempfile
import logging
import json
import re

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
    logger.info("✅ OpenAI API key loaded successfully")


# ============================================
# 🎯 CONFIGURATION PARAMETERS (Adjustable)
# ============================================

class STTConfig:
    """
    Centralized configuration for STT correction system
    Adjust these parameters for optimal performance
    """
    
    # Feature toggles
    ENABLE_CORRECTION = True  # 🔧 Master switch for correction feature
    
    # Correction model settings
    CORRECTION_MODEL = "gpt-4o-mini"  # 🔧 Options: "gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"
    CORRECTION_TEMPERATURE = 0.1  # 🔧 Lower = more conservative (0.0-1.0)
    CORRECTION_MAX_TOKENS = 200  # 🔧 Max tokens for correction response
    
    # Performance settings
    CORRECTION_TIMEOUT = 3.0  # 🔧 Max seconds for correction API call (affects speed)
    USE_STREAMING = False  # 🔧 Enable streaming for faster perceived response
    
    # Context settings
    USE_CONVERSATION_CONTEXT = True  # 🔧 Use chat history for better corrections
    MAX_CONTEXT_MESSAGES = 3  # 🔧 Number of previous messages to include
    
    # Validation settings
    MIN_TEXT_LENGTH = 2  # 🔧 Minimum characters to process
    VALIDATE_THAI_ONLY = True  # 🔧 Ensure output is Thai language
    
    # Medical terms database (expandable)
    COMMON_MEDICAL_TERMS = [
        "อาการ", "ปวด", "ปวดหัว", "ปวดท้อง", "ปวดหลัง",
        "ไข้", "คลื่นไส้", "อาเจียน", "ท้องเสีย", "ท้องผูก",
        "แพ้", "แพ้ยา", "แพ้อาหาร", "แพ้อากาศ",
        "เบาหวาน", "ความดัน", "หอบหืด", "ภูมิแพ้",
        "โรค", "โรคประจำตัว", "ประวัติ", "ครอบครัว",
        "ตรวจ", "วินิจฉัย", "รักษา", "ยา", "กินยา",
        "ผื่น", "คัน", "บวม", "เจ็บ", "จุกเสียด",
        "เหนื่อย", "หอบ", "เจ็บหน้าอก", "ใจสั่น"
    ]

# Global config instance
stt_config = STTConfig()


# ============================================
# 🧠 CORRECTION SYSTEM
# ============================================

def build_correction_prompt(
    transcribed_text: str,
    conversation_context: Optional[str] = None
) -> str:
    """
    Build optimized prompt for medical terminology correction
    
    Args:
        transcribed_text: Raw Whisper transcription
        conversation_context: Recent chat history for context
    
    Returns:
        Correction prompt for GPT
    """
    
    prompt = f"""คุณเป็นผู้เชี่ยวชาญในการแก้ไขข้อความทางการแพทย์ภาษาไทย

งานของคุณ: แก้ไขข้อความที่ถอดเสียงมาจากการสนทนาระหว่างแพทย์กับผู้ป่วย

ข้อความที่ต้องแก้ไข: "{transcribed_text}"
"""

    if conversation_context and stt_config.USE_CONVERSATION_CONTEXT:
        prompt += f"\n\nบริบทการสนทนา:\n{conversation_context}\n"
    
    prompt += """
กฎการแก้ไข:
1. แก้ไขเฉพาะคำที่สะกดผิดหรือคำที่ไม่มีความหมาย
2. รักษาความหมายและความตั้งใจเดิมของผู้พูด
3. ใช้คำศัพท์ทางการแพทย์ที่ถูกต้อง
4. ต้องเป็นภาษาไทยเท่านั้น ห้ามมีภาษาอังกฤษหรือตัวเลขที่ไม่จำเป็น
5. ถ้าข้อความถูกต้องอยู่แล้ว ให้คืนค่าเหมือนเดิม
6. ห้ามเพิ่มหรือลบข้อมูลที่สำคัญ
7. ใช้น้ำเสียงและลีลาของผู้พูดเดิม
8. อิงอ้างคำศัพท์ที่แก้จากความหมายรูปประโยค

ตัวอย่าง:
- "ปวดหัวมาก" → "ปวดหัวมาก" (ถูกต้องอยู่แล้ว)
- "ปวทหัว" → "ปวดหัว"
- "ผมมีอาการปวดท้องครับ" → "ผมมีอาการปวดท้องครับ"
- "เป็นไขัมากครับ" → "เป็นไข้มากครับ"
- "เคยสี่หรืออึบ้างมั้ย" → "เคยฉี่หรืออึบ้างมั้ย"

ตอบเฉพาะข้อความที่แก้ไขแล้ว ไม่ต้องอธิบาย:"""

    return prompt


async def correct_transcription(
    text: str,
    conversation_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Correct medical terminology and misspellings using GPT
    
    Args:
        text: Transcribed text from Whisper
        conversation_context: Recent conversation for context
    
    Returns:
        Dict with corrected text and metadata
    """
    
    # Check if correction is enabled
    if not stt_config.ENABLE_CORRECTION:
        logger.info("🔧 Correction disabled - returning original text")
        return {
            "corrected_text": text,
            "original_text": text,
            "was_corrected": False,
            "correction_applied": False
        }
    
    # Skip correction for very short text
    if len(text.strip()) < stt_config.MIN_TEXT_LENGTH:
        logger.info(f"⏭️ Text too short ({len(text)} chars) - skipping correction")
        return {
            "corrected_text": text,
            "original_text": text,
            "was_corrected": False,
            "reason": "text_too_short"
        }
    
    try:
        logger.info(f"🧠 Starting correction for: '{text[:50]}...'")
        start_time = __import__('time').time()
        
        # Build prompt
        prompt = build_correction_prompt(text, conversation_context)
        
        # Call GPT for correction with timeout
        response = openai.chat.completions.create(
            model=stt_config.CORRECTION_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "คุณเป็นผู้เชี่ยวชาญด้านภาษาไทยและคำศัพท์ทางการแพทย์"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=stt_config.CORRECTION_TEMPERATURE,
            max_tokens=stt_config.CORRECTION_MAX_TOKENS,
            timeout=stt_config.CORRECTION_TIMEOUT
        )
        
        corrected_text = response.choices[0].message.content.strip()
        
        # Remove quotes if GPT added them
        corrected_text = corrected_text.strip('"\'')
        
        # Validate Thai language only
        if stt_config.VALIDATE_THAI_ONLY:
            # Allow Thai characters, spaces, and common punctuation
            if not re.match(r'^[\u0E00-\u0E7Fๅฯ\s.,!?()]+$', corrected_text):
                logger.warning("⚠️ Correction contains non-Thai characters - using original")
                corrected_text = text
        
        elapsed_time = __import__('time').time() - start_time
        was_corrected = corrected_text != text
        
        logger.info(f"✅ Correction complete in {elapsed_time:.2f}s")
        logger.info(f"   Original:  '{text}'")
        logger.info(f"   Corrected: '{corrected_text}'")
        logger.info(f"   Changed: {'YES' if was_corrected else 'NO'}")
        
        return {
            "corrected_text": corrected_text,
            "original_text": text,
            "was_corrected": was_corrected,
            "correction_applied": True,
            "model_used": stt_config.CORRECTION_MODEL,
            "processing_time_ms": round(elapsed_time * 1000, 2)
        }
        
    except openai.APITimeoutError as e:
        logger.warning(f"⏱️ Correction timeout - using original text: {str(e)}")
        return {
            "corrected_text": text,
            "original_text": text,
            "was_corrected": False,
            "error": "timeout",
            "fallback": True
        }
    
    except Exception as e:
        logger.error(f"❌ Correction error: {str(e)}")
        # Fallback to original text on error
        return {
            "corrected_text": text,
            "original_text": text,
            "was_corrected": False,
            "error": str(e),
            "fallback": True
        }


# ============================================
# 📡 API ENDPOINTS
# ============================================

@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    conversation_context: Optional[str] = Body(None),
    enable_correction: Optional[bool] = Body(None)
) -> Dict[str, Any]:
    """
    Transcribe audio to text with optional correction
    
    Args:
        audio: Audio file (webm, mp4, wav, ogg)
        conversation_context: Recent chat history for better corrections
        enable_correction: Override global correction setting
    
    Returns:
        Transcription with optional correction results
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
        
        logger.info(f"📊 Received audio: {audio.filename}, size: {file_size_mb:.2f} MB")
        
        if file_size_mb > 25:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "file_too_large",
                    "message": f"ไฟล์เสียงใหญ่เกินไป ({file_size_mb:.2f} MB)",
                    "max_size_mb": 25
                }
            )
        
        if file_size_mb < 0.001:  # Less than 1KB
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "file_too_small",
                    "message": "ไฟล์เสียงเล็กเกินไป กรุณาบันทึกเสียงใหม่"
                }
            )
        
        # ============ STEP 2: WHISPER TRANSCRIPTION (Fast) ============
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
            logger.info(f"🎤 Starting Whisper transcription...")
            whisper_start = __import__('time').time()
            
            with open(temp_file_path, 'rb') as audio_file:
                transcript = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="th",
                    response_format="json",
                    temperature=0.0,
                    prompt="นี่คือการสนทนาทางการแพทย์เกี่ยวกับอาการของผู้ป่วย ใช้คำศัพท์ทางการแพทย์ภาษาไทย"
                )
            
            whisper_time = __import__('time').time() - whisper_start
            transcribed_text = transcript.text.strip()
            
            logger.info(f"✅ Whisper done in {whisper_time:.2f}s: '{transcribed_text[:100]}...'")
            
            # ============ STEP 4: CHECK FOR EMPTY AUDIO ============
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
                        "message": "ไม่พบเสียงพูดในการบันทึก กรุณาพูดให้ชัดเจน"
                    }
                )
            
            # ============ STEP 4: CORRECTION (Optional, Fast) ============
            correction_result = None
            final_text = transcribed_text
            
            # Use parameter override or global setting
            should_correct = enable_correction if enable_correction is not None else stt_config.ENABLE_CORRECTION
            
            if should_correct:
                logger.info("🧠 Applying correction...")
                correction_result = await correct_transcription(
                    transcribed_text,
                    conversation_context
                )
                final_text = correction_result["corrected_text"]
            else:
                logger.info("⏭️ Correction disabled - using raw transcription")
            
            # ============ STEP 5: PREPARE RESPONSE ============
            total_time = __import__('time').time() - whisper_start
            
            response_data = {
                "text": final_text,
                "original_transcription": transcribed_text,
                "language": "th",
                "whisper_model": "whisper-1",
                "file_size_mb": round(file_size_mb, 2),
                "processing_time": {
                    "whisper_ms": round(whisper_time * 1000, 2),
                    "total_ms": round(total_time * 1000, 2)
                }
            }
            
            # Add correction metadata if applied
            if correction_result:
                response_data["correction"] = correction_result
            
            logger.info(f"✅ STT pipeline complete in {total_time:.2f}s")
            logger.info(f"   Final text: '{final_text}'")
            
            return {
                "success": True,
                "data": response_data,
                "message": "Transcription completed successfully"
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    except HTTPException:
        raise
    
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
            "service": "OpenAI Whisper + GPT Correction",
            "whisper_model": "whisper-1",
            "correction_model": stt_config.CORRECTION_MODEL,
            "language": "th",
            "api_key_configured": api_key_configured,
            "max_file_size_mb": 25,
            "supported_formats": ["webm", "mp4", "mpeg", "wav", "ogg"],
            "features": {
                "whisper_transcription": True,
                "correction_enabled": stt_config.ENABLE_CORRECTION,
                "context_aware": stt_config.USE_CONVERSATION_CONTEXT,
                "thai_validation": stt_config.VALIDATE_THAI_ONLY
            },
            "configuration": {
                "correction_model": stt_config.CORRECTION_MODEL,
                "correction_temperature": stt_config.CORRECTION_TEMPERATURE,
                "correction_timeout": stt_config.CORRECTION_TIMEOUT,
                "max_context_messages": stt_config.MAX_CONTEXT_MESSAGES
            }
        },
        "message": "STT service is ready" if api_key_configured else "OpenAI API key not configured"
    }


@router.get("/health")
async def stt_health() -> Dict[str, Any]:
    """Health check endpoint for STT service"""
    api_key_configured = bool(openai.api_key)
    
    return {
        "status": "healthy" if api_key_configured else "degraded",
        "api_available": api_key_configured,
        "service": "STT",
        "components": {
            "whisper": api_key_configured,
            "correction": stt_config.ENABLE_CORRECTION and api_key_configured,
            "validation": True
        }
    }


@router.post("/config")
async def update_stt_config(config_update: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update STT configuration at runtime
    
    Example request body:
    {
        "enable_correction": true,
        "correction_model": "gpt-4o-mini",
        "correction_temperature": 0.1,
        "use_conversation_context": true
    }
    """
    
    updated_fields = []
    
    if "enable_correction" in config_update:
        stt_config.ENABLE_CORRECTION = bool(config_update["enable_correction"])
        updated_fields.append("enable_correction")
    
    if "correction_model" in config_update:
        stt_config.CORRECTION_MODEL = config_update["correction_model"]
        updated_fields.append("correction_model")
    
    if "correction_temperature" in config_update:
        stt_config.CORRECTION_TEMPERATURE = float(config_update["correction_temperature"])
        updated_fields.append("correction_temperature")
    
    if "correction_timeout" in config_update:
        stt_config.CORRECTION_TIMEOUT = float(config_update["correction_timeout"])
        updated_fields.append("correction_timeout")
    
    if "use_conversation_context" in config_update:
        stt_config.USE_CONVERSATION_CONTEXT = bool(config_update["use_conversation_context"])
        updated_fields.append("use_conversation_context")
    
    if "max_context_messages" in config_update:
        stt_config.MAX_CONTEXT_MESSAGES = int(config_update["max_context_messages"])
        updated_fields.append("max_context_messages")
    
    logger.info(f"🔧 Configuration updated: {updated_fields}")
    
    return {
        "success": True,
        "message": f"Updated {len(updated_fields)} configuration fields",
        "updated_fields": updated_fields,
        "current_config": {
            "enable_correction": stt_config.ENABLE_CORRECTION,
            "correction_model": stt_config.CORRECTION_MODEL,
            "correction_temperature": stt_config.CORRECTION_TEMPERATURE,
            "correction_timeout": stt_config.CORRECTION_TIMEOUT,
            "use_conversation_context": stt_config.USE_CONVERSATION_CONTEXT,
            "max_context_messages": stt_config.MAX_CONTEXT_MESSAGES
        }
    }