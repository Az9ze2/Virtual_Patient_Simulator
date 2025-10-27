"""
Text-to-Speech Service using OpenAI TTS API
Converts chatbot responses to audio with customizable voices
"""

import os
import base64
from typing import Literal, Optional
from io import BytesIO
from openai import OpenAI
from dotenv import load_dotenv

# Voice types available in OpenAI TTS
VoiceType = Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

class TTSService:
    """Service for converting text to speech using OpenAI TTS"""
    
    def __init__(self):
        """Initialize TTS service with OpenAI client"""
        load_dotenv()
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Default configuration
        self.default_model = "tts-1"  # or "tts-1-hd" for higher quality
        self.default_voice = "nova"  # female voice, good for Thai medical scenarios
        self.default_speed = 1.0  # normal speed (0.25 to 4.0)
    
    def text_to_speech(
        self,
        text: str,
        voice: VoiceType = None,
        model: str = None,
        speed: float = None,
        output_format: str = "mp3"
    ) -> bytes:
        """
        Convert text to speech
        
        Args:
            text: The text to convert to speech
            voice: Voice type (alloy, echo, fable, onyx, nova, shimmer)
            model: TTS model (tts-1 or tts-1-hd)
            speed: Speech speed (0.25 to 4.0)
            output_format: Audio format (mp3, opus, aac, flac)
        
        Returns:
            Audio data as bytes
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Use defaults if not specified
        voice = voice or self.default_voice
        model = model or self.default_model
        speed = speed or self.default_speed
        
        # Validate speed
        if not 0.25 <= speed <= 4.0:
            raise ValueError("Speed must be between 0.25 and 4.0")
        
        try:
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                speed=speed,
                response_format=output_format
            )
            
            # Return audio bytes
            return response.content
            
        except Exception as e:
            raise Exception(f"TTS generation failed: {str(e)}")
    
    def text_to_speech_base64(
        self,
        text: str,
        voice: VoiceType = None,
        model: str = None,
        speed: float = None,
        output_format: str = "mp3"
    ) -> str:
        """
        Convert text to speech and return as base64 string
        
        Args:
            text: The text to convert to speech
            voice: Voice type
            model: TTS model
            speed: Speech speed
            output_format: Audio format
        
        Returns:
            Base64 encoded audio string
        """
        audio_bytes = self.text_to_speech(text, voice, model, speed, output_format)
        return base64.b64encode(audio_bytes).decode('utf-8')
    
    def get_available_voices(self) -> dict:
        """
        Get available voice options with descriptions
        
        Returns:
            Dictionary of voice names and descriptions
        """
        return {
            "alloy": "Neutral, versatile voice",
            "echo": "Male voice, clear and articulate",
            "fable": "British accent, expressive",
            "onyx": "Deep male voice, authoritative",
            "nova": "Female voice, warm and friendly (recommended for patients)",
            "shimmer": "Female voice, soft and gentle"
        }

# Create singleton instance
tts_service = TTSService()

