"""
Enhanced Speech-to-Text (STT) Routes with Word Correction
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
    
    Parameters:
    - audio: Audio file (webm, mp4, mpeg, wav, ogg)
    - enable_correction: Whether to apply word correction (default: True)
    - conversation_context: Optional context for better correction
    
    Returns:
    - success: Boolean indicating success
    - data: Object containing transcribed text, corrected text, and metadata
    - message: Status message
    """
    
    # Check if API key is available
    if not openai.api_key:
        raise HTTPException(
            status_code=500,
            detail="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
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
                detail=f"Unsupported audio format: {audio.content_type}"
            )
        
        # Read and validate file size
        content = await audio.read()
        file_size_mb = len(content) / (1024 * 1024)
        
        logger.info(f"📊 Received audio: {audio.filename}, size: {file_size_mb:.2f} MB, type: {audio.content_type}")
        
        if file_size_mb > 25:
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {file_size_mb:.2f} MB. Maximum size is 25 MB."
            )
        
        if file_size_mb < 0.001:
            raise HTTPException(
                status_code=400,
                detail="Audio file is too small or empty."
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
            
            transcribed_text = transcript.text
            logger.info(f"✅ Whisper transcription: {transcribed_text[:100]}...")
            
            # ============ STEP 4: WORD CORRECTION (Optional) ============
            correction_result = None
            final_text = transcribed_text
            
            if enable_correction:
                logger.info(f"🔧 Applying word correction...")
                correction_result = word_correction_service.correct_text(
                    transcribed_text=transcribed_text,
                    context=conversation_context or ""
                )
                final_text = correction_result["corrected_text"]
                
                if correction_result["corrections_made"]:
                    logger.info(f"📝 Corrections applied: {correction_result['changes']}")
                else:
                    logger.info(f"✓ No corrections needed")
            
            # ============ STEP 5: PREPARE RESPONSE ============
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
    
    except openai.APIError as e:
        logger.error(f"🚨 OpenAI API Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"OpenAI API error: {str(e)}"
        )
    
    except openai.RateLimitError as e:
        logger.error(f"🚨 Rate Limit Error: {str(e)}")
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    
    except openai.APIConnectionError as e:
        logger.error(f"🚨 Connection Error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Failed to connect to OpenAI API."
        )
    
    except Exception as e:
        logger.error(f"🚨 Transcription Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to transcribe audio: {str(e)}"
        )


@router.get("/status")
async def stt_status() -> Dict[str, Any]:
    """
    Check STT service status and configuration
    
    Returns:
    - success: Boolean indicating if service is ready
    - data: Service configuration details
    - message: Status message
    """
    
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
                "context_aware": True
            },
            "optimal_settings": {
                "sample_rate": "16kHz",
                "channels": "mono",
                "bit_rate": "128kbps",
                "temperature": 0.0,
                "echo_cancellation": True,
                "noise_suppression": True
            }
        },
        "message": "STT service with word correction is ready" if api_key_configured else "OpenAI API key not configured"
    }


@router.get("/health")
async def stt_health() -> Dict[str, Any]:
    """
    Health check endpoint for STT service
    
    Returns:
    - status: Service health status
    - api_available: Whether OpenAI API is accessible
    """
    
    api_key_configured = bool(openai.api_key)
    
    return {
        "status": "healthy" if api_key_configured else "degraded",
        "api_available": api_key_configured,
        "service": "STT + Word Correction",
        "components": {
            "whisper": api_key_configured,
            "word_correction": api_key_configured
        }
    }


# ============ PIPELINE DOCUMENTATION ============
"""
📋 STT PIPELINE WITH WORD CORRECTION

🎯 PIPELINE FLOW:

1. 🎤 Audio Input
   └─> User records voice in Thai language
   └─> Audio file (webm/mp4/wav/mp3)

2. 🔊 Whisper STT (OpenAI)
   └─> Transcribe audio to text
   └─> Optimized for Thai medical terminology
   └─> Output: Raw transcribed text

3. 🔧 Word Correction AI (GPT-4o-mini)
   └─> Correct medical terms
   └─> Fix common STT errors
   └─> Preserve original meaning
   └─> Output: Corrected text

4. 💬 Main Chatbot
   └─> Receive corrected text
   └─> Generate response
   └─> Continue conversation

⚡ FEATURES:

✅ Medical Terminology Correction
   - ไข้, ปวดหัว, ท้องเสีย, etc.
   
✅ Common STT Error Fixes
   - Homophones: "ไข้" vs "ขาย"
   - Similar sounds: "ปวด" vs "บวม"
   
✅ Context-Aware Correction
   - Uses conversation history
   - Medical domain knowledge
   
✅ Meaning Preservation
   - No added information
   - Original intent maintained
   - Tone preserved

💰 COST OPTIMIZATION:

- Whisper: $0.006 per minute
- Word Correction: ~$0.0001 per correction
- Total: ~$0.0061 per 30-second message

📊 EXPECTED PERFORMANCE:

- Whisper Accuracy: 90-95% (Thai)
- Correction Improvement: +5-10%
- Final Accuracy: 95-98%
- Processing Time: 2-5 seconds

🔧 CONFIGURATION:

- enable_correction: True/False
- conversation_context: Optional string
- Whisper temperature: 0.0 (deterministic)
- Correction temperature: 0.1 (minimal creativity)
"""