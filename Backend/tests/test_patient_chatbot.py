#!/usr/bin/env python3
"""
Test script for Thai Medical Patient Chatbot
Tests both SCB-X Typhoon API and HuggingFace models
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.patient_chatbot import ThaiMedicalChatbot, ChatbotAPI

def test_chatbot_initialization():
    """Test chatbot initialization with different models"""
    
    print("🤖 Testing Thai Medical Chatbot Initialization")
    print("=" * 60)
    
    # Test HuggingFace model initialization
    print("\n1. Testing HuggingFace model initialization...")
    try:
        chatbot = ThaiMedicalChatbot(model_type="huggingface")
        print("✅ HuggingFace chatbot initialized successfully!")
        print(f"   Model type: {chatbot.model_type}")
    except Exception as e:
        print(f"❌ HuggingFace initialization failed: {str(e)}")
        print("Note: This is expected if HuggingFace transformers is not installed")
    
    # Test Ollama initialization
    print("\n2. Testing Ollama (SCB-X Typhoon) initialization...")
    try:
        chatbot = ThaiMedicalChatbot(
            model_type="ollama", 
            ollama_model="typhoon-v1.5x-70b-instruct",
            ollama_host="http://localhost:11434"
        )
        print("✅ Ollama chatbot initialized successfully!")
        print(f"   Model type: {chatbot.model_type}")
        print(f"   Ollama model: {chatbot.ollama_model}")
        print(f"   Ollama host: {chatbot.ollama_host}")
    except Exception as e:
        print(f"❌ Ollama initialization failed: {str(e)}")
        print("Note: This is expected if Ollama is not running or model not available")

def test_pattern_responses():
    """Test pattern-based responses (works without API keys)"""
    
    print("\n🎭 Testing Pattern-Based Responses")
    print("=" * 60)
    
    # Sample patient data
    sample_patient = {
        "patient_demographics": {
            "patient_name": "ด.ช.ยินดี ปรีดา",
            "age": "5 วัน",
            "gender": "ชาย",
            "relationship": "มารดาพามา"
        },
        "presenting_complaint": {
            "chief_complaint": "หัวนมข้างขวาแตก และปรึกษาเรื่องการให้นมแม่",
            "duration": "2 วันหลังคลอด",
            "severity": "เจ็บเวลาทารกดูดนม"
        },
        "current_status": {
            "general_condition": "ทารกสบายดี น้ำหนัก 3200 กรัม",
            "feeding_pattern": {
                "breast_milk": "ทุก 3 ชั่วโมง ครั้งละ 15-20 นาทีี"
            }
        },
        "patient_personality": {
            "communication_style": "มารดาใหม่ กังวลเล็กน้อย",
            "anxiety_level": "medium",
            "cooperation_level": "good"
        }
    }
    
    try:
        chatbot = ThaiMedicalChatbot(model_type="huggingface")  # Will fall back to patterns
        state = chatbot.initialize_conversation(sample_patient)
        
        print(f"\n👶 Patient: {sample_patient['patient_demographics']['patient_name']}")
        print(f"📋 Chief Complaint: {sample_patient['presenting_complaint']['chief_complaint']}")
        print(f"😊 Patient Mood: {state.patient_mood}")
        
        # Test different types of questions
        test_questions = [
            ("greeting", "สวัสดีครับ วันนี้มาโรงพยาบาลเพราะอะไรครับ?"),
            ("feeding", "ลูกกินนมเป็นอย่างไรครับ?"),
            ("timeline", "เริ่มมีอาการเมื่อไหร่ครับ?"),
            ("family_history", "ในครอบครัวมีประวัติโรคอะไรไหมครับ?"),
            ("general", "รู้สึกเป็นอย่างไรบ้างครับ?")
        ]
        
        print(f"\n💬 Testing conversation responses:")
        for question_type, question in test_questions:
            try:
                response, updated_state = chatbot.generate_response(question, state)
                state = updated_state
                
                print(f"\n👨‍⚕️ Doctor: {question}")
                print(f"🤱 Patient: {response}")
                print(f"   Question type: {question_type}")
                
            except Exception as e:
                print(f"❌ Failed for {question_type}: {str(e)}")
        
        # Show conversation analysis
        analysis = chatbot.get_conversation_analysis(state)
        print(f"\n📊 Conversation Analysis:")
        print(f"   Questions asked: {analysis['questions_asked']}")
        print(f"   Topics covered: {len(analysis['topics_covered'])}")
        print(f"   Information revealed: {len(analysis['information_revealed'])}")
        print(f"   Final mood: {analysis['final_patient_mood']}")
        print(f"   Quality feedback: {', '.join(analysis['quality_feedback'])}")
        
    except Exception as e:
        print(f"❌ Pattern response test failed: {str(e)}")

def test_chatbot_api():
    """Test the ChatbotAPI wrapper"""
    
    print("\n🔧 Testing ChatbotAPI Wrapper")
    print("=" * 60)
    
    sample_patient = {
        "patient_demographics": {
            "patient_name": "นางสาวใจดี",
            "age": "25 ปี",
            "gender": "หญิง",
            "relationship": "ตัวผู้ป่วยเอง"
        },
        "presenting_complaint": {
            "chief_complaint": "ปวดหัวมาก 3 วัน",
            "duration": "3 วัน",
            "severity": "รุนแรง"
        },
        "patient_personality": {
            "communication_style": "สุภาพ",
            "anxiety_level": "high",
            "cooperation_level": "good"
        }
    }
    
    try:
        # Initialize API with Ollama model (will fall back to patterns if not available)
        chatbot_api = ChatbotAPI(
            model_type="ollama",
            ollama_model="typhoon-v1.5x-70b-instruct",
            ollama_host="http://localhost:11434"
        )
        
        # Start session
        session_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session_result = chatbot_api.start_session(session_id, sample_patient)
        
        print(f"✅ Session started: {session_result['session_id']}")
        print(f"📝 Initial message: {session_result['initial_message']}")
        print(f"👤 Patient info: {session_result['patient_info']['name']}, {session_result['patient_info']['age']}")
        
        # Test conversation
        test_message = "สวัสดีครับ วันนี้มาหาหมอเพราะอะไรครับ?"
        response = chatbot_api.process_message(session_id, test_message)
        
        if response['status'] == 'success':
            print(f"\n👨‍⚕️ Doctor: {test_message}")
            print(f"🤒 Patient: {response['patient_response']}")
            print(f"📊 Stats: {response['conversation_stats']}")
        else:
            print(f"❌ Chat failed: {response.get('error', 'Unknown error')}")
        
        # End session
        end_result = chatbot_api.end_session(session_id)
        if end_result['status'] == 'completed':
            print(f"\n🏁 Session ended successfully")
            print(f"📋 Final summary: {end_result['final_summary']}")
        
    except Exception as e:
        print(f"❌ ChatbotAPI test failed: {str(e)}")

def test_thai_language_processing():
    """Test Thai language specific features"""
    
    print("\n🇹🇭 Testing Thai Language Processing")
    print("=" * 60)
    
    try:
        chatbot = ThaiMedicalChatbot(model_type="huggingface")
        
        # Test Thai medical vocabulary recognition
        thai_questions = [
            "ปวดหัวมาก",
            "เจ็บท้อง",
            "มีไข้ไหม",
            "กินยาอะไรบ้าง",
            "เมื่อไหร่เริ่มมีอาการ"
        ]
        
        print("🔍 Testing question analysis:")
        for question in thai_questions:
            question_type = chatbot._analyze_question(question)
            print(f"   '{question}' → {question_type}")
        
        # Test politeness markers
        sample_patient = {
            "patient_demographics": {
                "gender": "หญิง",
                "relationship": "มารดา"
            }
        }
        
        from src.patient_chatbot import ConversationState
        state = ConversationState(patient_data=sample_patient)
        
        test_responses = [
            "มีอาการปวดหัว",
            "ไม่ทราบ",
            "เจ็บมาก"
        ]
        
        print(f"\n✨ Testing politeness enhancement:")
        for response in test_responses:
            polished = chatbot._polish_response(response, state)
            print(f"   '{response}' → '{polished}'")
            
    except Exception as e:
        print(f"❌ Thai language test failed: {str(e)}")

def test_different_patient_types():
    """Test responses for different patient types"""
    
    print("\n👥 Testing Different Patient Types")
    print("=" * 60)
    
    patient_types = [
        {
            "name": "Anxious Mother",
            "data": {
                "patient_demographics": {"relationship": "มารดา", "gender": "หญิง"},
                "presenting_complaint": {"chief_complaint": "ลูกมีไข้สูง"},
                "patient_personality": {"anxiety_level": "high"}
            }
        },
        {
            "name": "Cooperative Adult",
            "data": {
                "patient_demographics": {"relationship": "ตัวผู้ป่วยเอง", "gender": "ชาย"},
                "presenting_complaint": {"chief_complaint": "มาตรวจสุขภาพ"},
                "patient_personality": {"anxiety_level": "low", "cooperation_level": "good"}
            }
        }
    ]
    
    try:
        chatbot = ThaiMedicalChatbot(model_type="huggingface")
        
        for patient_type in patient_types:
            print(f"\n👤 Testing {patient_type['name']}:")
            
            state = chatbot.initialize_conversation(patient_type['data'])
            print(f"   Initial mood: {state.patient_mood}")
            
            # Test greeting
            response, updated_state = chatbot.generate_response(
                "สวัสดีครับ วันนี้มาโรงพยาบาลเพราะอะไรครับ?", 
                state
            )
            print(f"   Response: {response}")
            
    except Exception as e:
        print(f"❌ Patient types test failed: {str(e)}")

if __name__ == "__main__":
    print("🏥 Thai Medical Chatbot Test Suite")
    print("==================================")
    
    # Run all tests
    test_chatbot_initialization()
    test_pattern_responses()
    test_chatbot_api()
    test_thai_language_processing()
    test_different_patient_types()
    
    print("\n🎉 All chatbot tests completed!")
    print("\nTo test with actual models:")
    print("• For HuggingFace: pip install transformers torch")
    print("• For SCB-X Typhoon (Ollama): Install Ollama and run:")
    print("    ollama pull typhoon-v1.5x-70b-instruct")
    print("    ollama serve (if not running as service)")
