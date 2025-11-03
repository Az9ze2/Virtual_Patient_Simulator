"""
TTS Router - Handle text-to-speech conversion
"""

import os
import sys
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from api.models.schemas import (
    TTSRequest, TTSResponse, APIResponse
)
from services.tts_service import tts_service

router = APIRouter()

@router.post("/generate", response_model=APIResponse)
async def generate_speech(request: TTSRequest):
    """
    Generate speech from text
    
    Parameters:
    - text: The text to convert to speech (max 4096 characters)
    - voice: Voice type (alloy, echo, fable, onyx, nova, shimmer)
    - model: TTS model (gpt-4o-mini-tts)
    - speed: Speech speed (0.25 to 4.0, default 1.0)
    - format: Audio format (mp3, opus, aac, flac)
    
    Returns:
    - Base64 encoded audio data
    """
    try:
        print(f"🔊 [TTS] Generating speech for text: {request.text[:100]}...")
        print(f"   🎤 Voice: {request.voice} | Model: {request.model} | Speed: {request.speed}x")
        
        # Generate audio as base64
        audio_base64 = tts_service.text_to_speech_base64(
            text=request.text,
            voice=request.voice.value if request.voice else None,
            model=request.model,
            speed=request.speed,
            output_format=request.format
        )
        
        print(f"   ✅ Audio generated successfully")
        
        return APIResponse(
            success=True,
            message="Speech generated successfully",
            data={
                "audio_base64": audio_base64,
                "format": request.format,
                "voice": request.voice.value if request.voice else "nova",
                "text_length": len(request.text)
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate speech: {str(e)}"
        )

@router.post("/generate-binary")
async def generate_speech_binary(request: TTSRequest):
    """
    Generate speech from text and return as binary audio file
    
    This endpoint returns the audio file directly instead of base64 encoding,
    useful for direct playback or download.
    
    Returns:
    - Audio file as binary response
    """
    try:
        print(f"🔊 [TTS] Generating binary audio for text: {request.text[:100]}...")
        
        # Generate audio as bytes
        audio_bytes = tts_service.text_to_speech(
            text=request.text,
            voice=request.voice.value if request.voice else None,
            model=request.model,
            speed=request.speed,
            output_format=request.format
        )
        
        # Determine media type
        media_types = {
            "mp3": "audio/mpeg",
            "opus": "audio/opus",
            "aac": "audio/aac",
            "flac": "audio/flac"
        }
        media_type = media_types.get(request.format, "audio/mpeg")
        
        print(f"   ✅ Binary audio generated successfully")
        
        return Response(
            content=audio_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename=speech.{request.format}"
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate speech: {str(e)}"
        )

@router.get("/voices")
async def get_available_voices():
    """
    Get list of available voices with descriptions
    
    Returns:
    - Dictionary of voice names and their descriptions
    """
    try:
        voices = tts_service.get_available_voices()
        
        return APIResponse(
            success=True,
            message="Available voices retrieved successfully",
            data={"voices": voices}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get voices: {str(e)}"
        )

@router.get("/health")
async def tts_health_check():
    """
    Check TTS service health
    
    Returns:
    - Service status and configuration
    """
    try:
        return APIResponse(
            success=True,
            message="TTS service is healthy",
            data={
                "service": "OpenAI TTS",
                "default_voice": tts_service.default_voice,
                "default_model": tts_service.default_model,
                "default_speed": tts_service.default_speed,
                "available_voices": list(tts_service.get_available_voices().keys()),
                "available_models": ["gpt-4o-mini-tts"],
                "available_formats": ["mp3", "opus", "aac", "flac"]
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"TTS service health check failed: {str(e)}"
        )

