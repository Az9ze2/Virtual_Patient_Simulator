"""
Enhanced TTS Router - Exposes patient-aware TTS generation
"""

import os
import sys
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from typing import Optional, Dict, Any
from pydantic import BaseModel

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from api.models.schemas import (
    TTSRequest, TTSResponse, APIResponse, VoiceType
)
from services.enhanced_tts_service import enhanced_tts_service

router = APIRouter()

class EnhancedTTSRequest(BaseModel):
    """Request model for patient-aware TTS"""
    text: str
    patient_info: Dict[str, Any]
    case_metadata: Optional[Dict[str, Any]] = None
    voice: Optional[VoiceType] = None
    model: str = "gpt-4o-mini-tts"
    speed: float = 1
    format: str = "mp3"
    use_personality_prompt: bool = True

@router.post("/generate", response_model=APIResponse)
async def generate_speech(request: TTSRequest):
    """
    Generate speech from text (basic version without patient context)
    
    Parameters:
    - text: The text to convert to speech (max 4096 characters)
    - voice: Voice type (alloy, echo, fable, onyx, nova, shimmer)
    - model: TTS model (gpt-4o-mini-tts)
    - speed: Speech speed (0.25 to 4.0, default 1)
    - format: Audio format (mp3, opus, aac, flac)
    
    Returns:
    - Base64 encoded audio data
    """
    try:
        print(f"🔊 [TTS] Generating speech for text: {request.text[:100]}...")
        print(f"   🎤 Voice: {request.voice} | Model: {request.model} | Speed: {request.speed}x")
        
        # Generate audio as base64
        audio_base64 = enhanced_tts_service.text_to_speech_base64(
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

@router.post("/generate-with-context", response_model=APIResponse)
async def generate_speech_with_context(request: EnhancedTTSRequest):
    """
    Generate speech with patient context and personality
    
    This endpoint uses patient information to:
    - Auto-select appropriate voice based on gender and age
    - Adjust speech speed based on age category
    - Generate personality-aware prompts for realistic delivery
    
    Parameters:
    - text: The text to convert to speech
    - patient_info: Patient information (name, age, sex, chief_complaint)
    - case_metadata: Optional case metadata for additional context
    - voice: Optional voice override (auto-selects if not provided)
    - model: TTS model
    - speed: Speech speed (auto-adjusts based on age if not overridden)
    - format: Audio format
    - use_personality_prompt: Enable personality-aware prompt enhancement
    
    Returns:
    - Base64 encoded audio with metadata about voice selection
    """
    try:
        print(f"🎭 [Enhanced TTS] Generating patient-aware speech")
        print(f"   👤 Patient: {request.patient_info.get('name', 'Unknown')}")
        print(f"   🎤 Personality prompt: {'Enabled' if request.use_personality_prompt else 'Disabled'}")
        
        # Generate audio with patient context
        audio_base64 = enhanced_tts_service.text_to_speech_base64_with_context(
            text=request.text,
            patient_info=request.patient_info,
            case_metadata=request.case_metadata,
            voice=request.voice.value if request.voice else None,
            model=request.model,
            speed=request.speed,
            output_format=request.format,
            use_personality_prompt=request.use_personality_prompt
        )
        
        # Get the voice that was selected
        selected_voice = (
            request.voice.value if request.voice 
            else enhanced_tts_service._select_voice_for_patient(request.patient_info)
        )
        
        print(f"   ✅ Audio generated with voice: {selected_voice}")
        
        return APIResponse(
            success=True,
            message="Patient-aware speech generated successfully",
            data={
                "audio_base64": audio_base64,
                "format": request.format,
                "voice_used": selected_voice,
                "voice_auto_selected": request.voice is None,
                "personality_enhanced": request.use_personality_prompt,
                "text_length": len(request.text),
                "patient_gender": request.patient_info.get('sex', 'unknown'),
                "patient_age": request.patient_info.get('age', 'unknown')
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
    (Without patient context - for general use)
    """
    try:
        print(f"🔊 [TTS] Generating binary audio for text: {request.text[:100]}...")
        
        # Generate audio as bytes
        audio_bytes = enhanced_tts_service.text_to_speech(
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
    """
    try:
        voices = enhanced_tts_service.get_available_voices()
        
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

@router.get("/voice-profiles")
async def get_voice_profiles():
    """
    Get voice profile mappings used for patient context
    Shows which voices are selected for different patient demographics
    """
    try:
        profiles = enhanced_tts_service.get_voice_profiles()
        
        return APIResponse(
            success=True,
            message="Voice profiles retrieved successfully",
            data={
                "profiles": profiles,
                "description": "Voice selection based on gender and age category"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get voice profiles: {str(e)}"
        )

@router.get("/health")
async def tts_health_check():
    """
    Check TTS service health with enhanced features
    """
    try:
        return APIResponse(
            success=True,
            message="Enhanced TTS service is healthy",
            data={
                "service": "OpenAI TTS Enhanced",
                "default_model": enhanced_tts_service.default_model,
                "default_speed": enhanced_tts_service.default_speed,
                "available_voices": list(enhanced_tts_service.get_available_voices().keys()),
                "available_models": ["gpt-4o-mini-tts"],
                "available_formats": ["mp3", "opus", "aac", "flac"],
                "features": [
                    "Gender-based voice selection",
                    "Age-based voice and speed adjustment",
                    "Personality-aware prompt generation",
                    "Thai language optimized",
                    "Symptom-based emotional tone"
                ],
                "voice_profiles": enhanced_tts_service.get_voice_profiles()
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"TTS service health check failed: {str(e)}"
        )