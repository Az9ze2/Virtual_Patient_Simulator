"""
Speech-to-Text (STT) Routes for Thai Language Recognition
Uses OpenAI Whisper API optimized for Thai medical conversations
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import openai
import os
from typing import Dict, Any
import tempfile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/stt", tags=["Speech-to-Text"])

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    logger.warning("⚠️  OPENAI_API_KEY not found! STT features will not work.")
else:
    logger.info("✓ OpenAI API key loaded successfully")


@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...)
) -> Dict[str, Any]:
    """
    Transcribe audio to text using OpenAI Whisper API
    Optimized for Thai language recognition
    
    Parameters:
    - audio: Audio file (webm, mp4, mpeg, wav, ogg)
    
    Returns:
    - success: Boolean indicating success
    - data: Object containing transcribed text and metadata
    - message: Status message
    """
    
    # Check if API key is available
    if not openai.api_key:
        raise HTTPException(
            status_code=500,
            detail="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
        )
    
    try:
        # Validate file type
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
                detail=f"Unsupported audio format: {audio.content_type}. Supported formats: webm, mp4, mpeg, wav, ogg"
            )
        
        # Read and validate file size
        content = await audio.read()
        file_size_mb = len(content) / (1024 * 1024)
        
        logger.info(f"📊 Received audio file: {audio.filename}, size: {file_size_mb:.2f} MB, type: {audio.content_type}")
        
        # Check file size limits
        if file_size_mb > 25:
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {file_size_mb:.2f} MB. Maximum size is 25 MB."
            )
        
        if file_size_mb < 0.001:  # Less than 1 KB
            raise HTTPException(
                status_code=400,
                detail="Audio file is too small or empty. Please record a longer message."
            )
        
        # Save to temporary file (Whisper API requires file path)
        # Determine file extension from content type
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
            # ============ WHISPER API CALL WITH OPTIMIZED PARAMETERS ============
            logger.info(f"🎤 Transcribing audio with Whisper API...")
            
            with open(temp_file_path, 'rb') as audio_file:
                # Call OpenAI Whisper API with Thai-optimized parameters
                transcript = openai.audio.transcriptions.create(
                    model="whisper-1",  # Whisper model (only one available)
                    file=audio_file,
                    language="th",  # ✅ CRITICAL: Specify Thai language for better accuracy
                    
                    # ============ OPTIMIZED PARAMETERS ============
                    response_format="json",  # ✅ RECOMMENDED: Returns JSON with text
                    temperature=0.0,  # ✅ RECOMMENDED: 0.0 for maximum accuracy
                    
                    # Optional prompt to guide transcription
                    # This helps with medical terminology and context
                    prompt="นี่คือการสนทนาทางการแพทย์เกี่ยวกับอาการของผู้ป่วย ใช้คำศัพท์ทางการแพทย์ภาษาไทย"
                )
            
            # Extract transcribed text
            transcribed_text = transcript.text
            
            logger.info(f"✅ Transcription successful: {transcribed_text[:100]}...")
            
            return {
                "success": True,
                "data": {
                    "text": transcribed_text,
                    "language": "th",
                    "model": "whisper-1",
                    "file_size_mb": round(file_size_mb, 2)
                },
                "message": "Transcription completed successfully"
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
            detail="Failed to connect to OpenAI API. Please check your internet connection."
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
    
    # Check if OpenAI API key is configured
    api_key_configured = bool(openai.api_key)
    
    return {
        "success": api_key_configured,
        "data": {
            "service": "OpenAI Whisper",
            "model": "whisper-1",
            "language": "th",
            "api_key_configured": api_key_configured,
            "max_file_size_mb": 25,
            "supported_formats": ["webm", "mp4", "mpeg", "wav", "ogg"],
            "optimal_settings": {
                "sample_rate": "16kHz",
                "channels": "mono",
                "bit_rate": "128kbps",
                "temperature": 0.0,
                "echo_cancellation": True,
                "noise_suppression": True
            }
        },
        "message": "STT service is ready" if api_key_configured else "OpenAI API key not configured"
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
        "service": "STT",
        "timestamp": None  # You can add timestamp if needed
    }


# ============ PARAMETER OPTIMIZATION GUIDE ============
"""
📋 WHISPER API PARAMETER OPTIMIZATION FOR THAI LANGUAGE

🎯 CRITICAL PARAMETERS:

1. language="th" (MOST IMPORTANT)
   - Forces Whisper to recognize Thai language
   - Without this, accuracy drops significantly
   - Whisper may default to English or other languages

2. temperature=0.0 (RECOMMENDED)
   - 0.0 = Most deterministic and accurate
   - Higher values (0.5-1.0) may introduce hallucinations
   - For medical use, always use 0.0

3. prompt (OPTIONAL but POWERFUL)
   - Provides context to improve accuracy
   - Helps with medical terminology
   - Example: "การสนทนาทางการแพทย์เกี่ยวกับอาการของผู้ป่วย"
   - Can include previous transcription for continuity

4. response_format="json" (RECOMMENDED)
   - Easy to parse in application
   - Other options: "text", "verbose_json", "srt", "vtt"

⚡ AUDIO QUALITY SETTINGS (CLIENT-SIDE):
- Sample Rate: 16kHz (Whisper's optimal rate)
- Channels: Mono (sufficient for speech)
- Bit Rate: 128kbps (good balance)
- Format: WebM with Opus codec (best compression)

💰 COST:
- $0.006 per minute of audio
- 30-second message = $0.003
- 100 messages/day ≈ $9/month

📊 EXPECTED PERFORMANCE:
- Processing time: 2-5 seconds for 30-second audio
- Accuracy: 90-95% for clear Thai speech
- Accuracy: 85-90% with background noise

🔧 TROUBLESHOOTING:
- If accuracy is low, try adjusting the prompt
- For very noisy audio, implement preprocessing
- For specialized vocabulary, include terms in prompt
"""