"""
Chatbot Router - Handle chat interactions with the unified chatbot
OPTIMIZED for natural Thai TTS with child patient handling
"""

import os
import sys
import time
from fastapi import APIRouter, HTTPException

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from api.models.schemas import (
    ChatMessage, ChatResponse, APIResponse, ChatMessageWithTTS
)
from api.utils.session_manager import session_manager
from services.enhanced_tts_service import enhanced_tts_service

router = APIRouter()

@router.post("/{session_id}/chat")
async def send_message(session_id: str, message: ChatMessage):
    """
    Send a message to the chatbot and get response
    """
    try:
        # Get session and chatbot
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
        
        # Log incoming message
        print(f"💬 [CHATBOT] Processing message from user: {message.message[:100]}...")
        print(f"   📋 Session: {session_id[:8]}... | Case: {chatbot.case_type} | Model: {chatbot.model_choice}")
        
        # Send message to chatbot
        start_time = time.time()
        response, response_time = chatbot.chat_turn(message.message)
        
        print(f"   🤖 Bot response: {response[:100]}...")
        print(f"   ⏱️ Response time: {response_time:.3f}s | Tokens: {chatbot.total_tokens}")
        
        # Update session chat history
        session_manager.update_chat_history(
            session_id=session_id,
            user_message=message.message,
            bot_response=response
        )
        
        return APIResponse(
            success=True,
            message="Message sent successfully",
            data={
                "response": response,
                "response_time": response_time,
                "session_id": session_id,
                "token_usage": {
                    "input_tokens": chatbot.input_tokens,
                    "output_tokens": chatbot.output_tokens,
                    "total_tokens": chatbot.total_tokens
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )

@router.post("/{session_id}/chat-with-tts")
async def send_message_with_tts(session_id: str, message: ChatMessageWithTTS):
    """
    Send a message to the chatbot and get response with optional TTS audio
    
    This endpoint extends the regular chat with TTS capabilities.
    If enable_tts is True, the response will include audio data.
    
    Enhanced features:
    - Natural Thai pronunciation optimization
    - Child patient special handling (mother speaks if age < 12)
    - Automatic voice selection based on patient demographics
    """
    try:
        # Get session and chatbot
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
        
        # Log incoming message
        tts_status = "with TTS" if message.enable_tts else "without TTS"
        print(f"💬 [CHATBOT] Processing message from user ({tts_status}): {message.message[:100]}...")
        print(f"   📋 Session: {session_id[:8]}... | Case: {chatbot.case_type} | Model: {chatbot.model_choice}")
        
        # Send message to chatbot
        start_time = time.time()
        response, response_time = chatbot.chat_turn(message.message)
        
        print(f"   🤖 Bot response: {response[:100]}...")
        print(f"   ⏱️ Response time: {response_time:.3f}s | Tokens: {chatbot.total_tokens}")
        
        # Update session chat history
        session_manager.update_chat_history(
            session_id=session_id,
            user_message=message.message,
            bot_response=response
        )
        
        # Prepare response data
        response_data = {
            "response": response,
            "response_time": response_time,
            "session_id": session_id,
            "token_usage": {
                "input_tokens": chatbot.input_tokens,
                "output_tokens": chatbot.output_tokens,
                "total_tokens": chatbot.total_tokens
            }
        }
        
        # Generate TTS if requested
        if message.enable_tts:
            try:
                print(f"   📊 Generating optimized TTS audio with patient context...")
                
                # Get patient info from session for context-aware TTS
                patient_info = {}
                if session.patient_info:
                    patient_info = session.patient_info.dict() if hasattr(session.patient_info, 'dict') else session.patient_info
                    print(f"   📋 [DEBUG] Patient info retrieved: {patient_info}")
                else:
                    print(f"   ⚠️ [WARNING] No patient_info in session, using defaults")
                
                case_metadata = getattr(session, 'case_metadata', {})
                
                # Get speaker role (determines if mother speaks for child)
                speaker_role = enhanced_tts_service.get_speaker_role(patient_info) if patient_info else 'patient'
                
                if patient_info:
                    age_display = patient_info.get('age', 'N/A')
                    if isinstance(age_display, dict):
                        age_display = age_display.get('value', 'N/A')
                    
                    print(f"   🎭 Patient: {patient_info.get('name', 'Unknown')} | "
                          f"Gender: {patient_info.get('sex', 'N/A')} | "
                          f"Age: {age_display}")
                    print(f"   👥 Speaker: {speaker_role.upper()}")
                
                # Use enhanced TTS with patient context and optimization
                audio_base64 = enhanced_tts_service.text_to_speech_base64_with_context(
                    text=response,
                    patient_info=patient_info,
                    case_metadata=case_metadata,
                    voice=message.voice.value if message.voice else None,  # Auto-select if None
                    speed=message.tts_speed,
                    output_format="mp3",
                    use_personality_prompt=True  # Enable personality enhancement
                )
                
                # Determine which voice was used
                if message.voice:
                    selected_voice = message.voice.value
                else:
                    selected_voice = enhanced_tts_service._select_voice_for_patient(patient_info) if patient_info else "nova"
                
                response_data["audio"] = {
                    "audio_base64": audio_base64,
                    "format": "mp3",
                    "voice": selected_voice,
                    "voice_auto_selected": message.voice is None,
                    "speed": message.tts_speed,
                    "speaker_role": speaker_role,  # 'mother' or 'patient'
                    "is_child_patient": speaker_role == 'mother',
                    "optimized_for_thai": True
                }
                
                speaker_label = "mother" if speaker_role == 'mother' else "patient"
                print(f"   ✅ TTS audio generated successfully")
                print(f"      Voice: {selected_voice} | Speaker: {speaker_label} | Optimized: YES")
                
            except Exception as tts_error:
                print(f"   ⚠️ TTS generation failed: {tts_error}")
                import traceback
                print(f"   🔍 Traceback: {traceback.format_exc()}")
                # Continue without TTS if it fails
                response_data["audio_error"] = str(tts_error)
        
        return APIResponse(
            success=True,
            message="Message sent successfully" + (" with optimized TTS audio" if message.enable_tts and "audio" in response_data else ""),
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )

@router.get("/{session_id}/patient-info")
async def get_patient_info(session_id: str):
    """
    Get patient information for examiner view
    """
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )
        
        if not session.patient_info:
            raise HTTPException(
                status_code=404,
                detail="Patient information not available"
            )
        
        return APIResponse(
            success=True,
            message="Patient information retrieved successfully",
            data={"patient_info": session.patient_info.dict()}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get patient info: {str(e)}"
        )

@router.get("/{session_id}/chat-history")
async def get_chat_history(session_id: str):
    """
    Get chat history for a session
    """
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )
        
        return APIResponse(
            success=True,
            message="Chat history retrieved successfully",
            data={
                "chat_history": session.chat_history,
                "message_count": len(session.chat_history)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get chat history: {str(e)}"
        )

@router.get("/{session_id}/token-usage")
async def get_token_usage(session_id: str):
    """
    Get current token usage for a session
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
        
        token_usage = {
            "input_tokens": chatbot.input_tokens,
            "output_tokens": chatbot.output_tokens,
            "total_tokens": chatbot.total_tokens
        }
        
        return APIResponse(
            success=True,
            message="Token usage retrieved successfully",
            data={"token_usage": token_usage}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get token usage: {str(e)}"
        )

@router.get("/{session_id}/chatbot-status")
async def get_chatbot_status(session_id: str):
    """
    Get chatbot status and configuration
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
        
        # Get patient info for voice profile and speaker role
        patient_info = session.patient_info.dict() if session.patient_info else {}
        selected_voice = None
        speaker_role = 'patient'
        
        if patient_info:
            selected_voice = enhanced_tts_service._select_voice_for_patient(patient_info)
            speaker_role = enhanced_tts_service.get_speaker_role(patient_info)
        
        # Get chatbot configuration and status
        status_data = {
            "model_choice": chatbot.model_choice,
            "memory_mode": chatbot.memory_mode,
            "case_type": chatbot.case_type,
            "display_name": chatbot.display_name,
            "generation_params": chatbot.generation_params,
            "message_history_length": len(chatbot.message_history),
            "questions_to_ask": len(chatbot.questions_to_ask) if hasattr(chatbot, 'questions_to_ask') else 0,
            "token_usage": {
                "input_tokens": chatbot.input_tokens,
                "output_tokens": chatbot.output_tokens,
                "total_tokens": chatbot.total_tokens
            },
            "tts_voice": selected_voice,
            "tts_speaker_role": speaker_role,  # 'mother' or 'patient'
            "tts_available": True,
            "tts_enhanced": True,
            "tts_optimized_for_thai": True
        }
        
        return APIResponse(
            success=True,
            message="Chatbot status retrieved successfully",
            data={"chatbot_status": status_data}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get chatbot status: {str(e)}"
        )