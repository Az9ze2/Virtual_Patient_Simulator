"""
Config Router - Handle configuration management for chatbot parameters
"""

import os
import sys
from fastapi import APIRouter, HTTPException

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from api.models.schemas import (
    APIResponse, ConfigUpdateRequest, SessionConfig, 
    ModelType, MemoryMode
)
from api.utils.session_manager import session_manager

router = APIRouter()

@router.get("/default")
async def get_default_config():
    """
    Get default configuration settings
    """
    try:
        default_config = SessionConfig()
        
        return APIResponse(
            success=True,
            message="Default configuration retrieved successfully",
            data={
                "config": default_config.dict(),
                "available_options": {
                    "models": [model.value for model in ModelType],
                    "memory_modes": [mode.value for mode in MemoryMode],
                    "temperature_range": {
                        "min": 0.0,
                        "max": 2.0,
                        "default": 0.7
                    }
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get default config: {str(e)}"
        )

@router.get("/models")
async def get_available_models():
    """
    Get list of available models with their capabilities
    """
    try:
        models_info = [
            {
                "name": "gpt-4.1-mini",
                "display_name": "GPT-4.1 Mini",
                "description": "Faster, tunable model with temperature and other parameter control",
                "supports_temperature": True,
                "supports_top_p": True,
                "supports_frequency_penalty": True,
                "supports_presence_penalty": True,
                "supports_seed": True,
                "default_temperature": 0.7
            },
            {
                "name": "gpt-5",
                "display_name": "GPT-5",
                "description": "Advanced deterministic model with limited parameter control",
                "supports_temperature": False,
                "supports_top_p": False,
                "supports_frequency_penalty": False,
                "supports_presence_penalty": False,
                "supports_seed": True,
                "default_temperature": None
            }
        ]
        
        return APIResponse(
            success=True,
            message="Available models retrieved successfully",
            data={"models": models_info}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get models: {str(e)}"
        )

@router.get("/memory-modes")
async def get_memory_modes():
    """
    Get available memory management modes
    """
    try:
        memory_modes = [
            {
                "name": "none",
                "display_name": "No Memory Management",
                "description": "Keep all conversation history (may hit token limits in long conversations)"
            },
            {
                "name": "truncate",
                "display_name": "Truncate Old Messages",
                "description": "Remove oldest messages when limit is reached"
            },
            {
                "name": "summarize", 
                "display_name": "Summarize History",
                "description": "Compress old conversation into summaries (recommended)"
            }
        ]
        
        return APIResponse(
            success=True,
            message="Memory modes retrieved successfully",
            data={"memory_modes": memory_modes}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get memory modes: {str(e)}"
        )

@router.get("/{session_id}")
async def get_session_config(session_id: str):
    """
    Get current configuration for a specific session
    """
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )
        
        chatbot = session_manager.get_chatbot(session_id)
        current_config = {
            "session_config": session.config.dict(),
            "chatbot_status": {
                "model_choice": chatbot.model_choice if chatbot else None,
                "memory_mode": chatbot.memory_mode if chatbot else None,
                "generation_params": chatbot.generation_params if chatbot else None,
                "case_type": chatbot.case_type if chatbot else None
            }
        }
        
        return APIResponse(
            success=True,
            message="Session configuration retrieved successfully",
            data=current_config
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session config: {str(e)}"
        )

@router.put("/{session_id}")
async def update_session_config(session_id: str, config_update: ConfigUpdateRequest):
    """
    Update configuration for an active session
    Note: Some changes may require session restart to take effect
    """
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )
        
        chatbot = session_manager.get_chatbot(session_id)
        if not chatbot:
            raise HTTPException(
                status_code=500,
                detail="Chatbot instance not found"
            )
        
        # Track what was updated
        updates_applied = []
        requires_restart = []
        
        # Update temperature (can be applied immediately for GPT-4.1-mini)
        if config_update.temperature is not None:
            session.config.temperature = config_update.temperature
            if chatbot.model_choice == "gpt-4.1-mini":
                chatbot.generation_params["temperature"] = config_update.temperature
                updates_applied.append("temperature")
            else:
                requires_restart.append("temperature (not supported by current model)")
        
        # Update exam mode (affects seed)
        if config_update.exam_mode is not None:
            session.config.exam_mode = config_update.exam_mode
            if config_update.exam_mode:
                chatbot.generation_params["seed"] = 1234
                updates_applied.append("exam_mode (seed set to 1234)")
            else:
                chatbot.generation_params.pop("seed", None)
                updates_applied.append("exam_mode (seed removed)")
        
        # Model and memory mode changes require restart
        if config_update.model_choice is not None:
            session.config.model_choice = config_update.model_choice
            requires_restart.append("model_choice")
        
        if config_update.memory_mode is not None:
            session.config.memory_mode = config_update.memory_mode
            requires_restart.append("memory_mode")
        
        return APIResponse(
            success=True,
            message="Configuration updated",
            data={
                "updated_config": session.config.dict(),
                "updates_applied": updates_applied,
                "requires_restart": requires_restart,
                "current_generation_params": chatbot.generation_params
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update session config: {str(e)}"
        )

@router.post("/validate")
async def validate_config(config: SessionConfig):
    """
    Validate a configuration without applying it
    """
    try:
        # Check model-specific parameter compatibility
        warnings = []
        errors = []
        
        if config.model_choice == ModelType.GPT_5:
            if config.temperature != 0.7:  # Not the default
                warnings.append("GPT-5 does not support temperature parameter - will be ignored")
        
        if config.temperature < 0.0 or config.temperature > 2.0:
            errors.append("Temperature must be between 0.0 and 2.0")
        
        # Validate combinations
        if config.exam_mode and config.model_choice == ModelType.GPT_5:
            # This is actually fine, both support seed
            pass
        
        validation_result = {
            "valid": len(errors) == 0,
            "config": config.dict(),
            "warnings": warnings,
            "errors": errors
        }
        
        return APIResponse(
            success=True,
            message="Configuration validation completed",
            data=validation_result
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate config: {str(e)}"
        )

@router.get("/presets/list")
async def get_config_presets():
    """
    Get predefined configuration presets
    """
    try:
        presets = [
            {
                "name": "practice_standard",
                "display_name": "Practice Mode (Standard)",
                "description": "Recommended settings for practice sessions",
                "config": SessionConfig(
                    model_choice=ModelType.GPT_4_1_MINI,
                    memory_mode=MemoryMode.SUMMARIZE,
                    temperature=0.7,
                    exam_mode=False
                ).dict()
            },
            {
                "name": "practice_creative",
                "display_name": "Practice Mode (Creative)",
                "description": "More varied responses for diverse practice",
                "config": SessionConfig(
                    model_choice=ModelType.GPT_4_1_MINI,
                    memory_mode=MemoryMode.SUMMARIZE,
                    temperature=0.9,
                    exam_mode=False
                ).dict()
            },
            {
                "name": "exam_mode",
                "display_name": "Exam Mode",
                "description": "Standardized responses for formal evaluation",
                "config": SessionConfig(
                    model_choice=ModelType.GPT_4_1_MINI,
                    memory_mode=MemoryMode.SUMMARIZE,
                    temperature=0.7,
                    exam_mode=True
                ).dict()
            },
            {
                "name": "gpt5_deterministic",
                "display_name": "GPT-5 Deterministic",
                "description": "Most consistent responses using GPT-5",
                "config": SessionConfig(
                    model_choice=ModelType.GPT_5,
                    memory_mode=MemoryMode.SUMMARIZE,
                    temperature=0.0,  # Will be ignored by GPT-5
                    exam_mode=True
                ).dict()
            }
        ]
        
        return APIResponse(
            success=True,
            message="Configuration presets retrieved successfully",
            data={"presets": presets}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get presets: {str(e)}"
        )
