"""
Services Module - Shared services for the Virtual Patient Simulator

This module contains reusable services that can be used across the application.
"""

from .tts_service import tts_service, TTSService
from .correction import WordCorrectionService

__all__ = ['tts_service', 'TTSService', 'WordCorrectionService']

