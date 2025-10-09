"""
Chatbot Router - Handle chat interactions with the unified chatbot
"""

import os
import sys
import time
from fastapi import APIRouter, HTTPException

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from api.models.schemas import (
    ChatMessage, ChatResponse, APIResponse
)
from api.utils.session_manager import session_manager

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
            }
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
