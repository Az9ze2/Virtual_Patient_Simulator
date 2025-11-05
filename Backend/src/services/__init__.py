"""
Services Module - Shared services for the Virtual Patient Simulator

This module contains reusable services that can be used across the application.
"""

from .tts_service import tts_service, TTSService
from .enhanced_tts_service import enhanced_tts_service, EnhancedTTSService

__all__ = ['tts_service', 'TTSService', 'enhanced_tts_service', 'EnhancedTTSService']