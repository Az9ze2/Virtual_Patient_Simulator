"""
Services Module - Shared services for the Virtual Patient Simulator

This module contains reusable services that can be used across the application.
"""

from .tts_service import tts_service, TTSService

__all__ = ['tts_service', 'TTSService']

