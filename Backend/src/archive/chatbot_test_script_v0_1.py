#!/usr/bin/env python3
"""
Simplified Thai Medical Chatbot Test Script
Basic functionality with token usage tracking

Usage:
    python chatbot_test_script.py

Requirements:
    - .env file with OPENAI_API_KEY
    - breast_feeding.json in the same directory
"""

import json
import time
import sys
import os
from typing import Dict, Any, Tuple
from dotenv import load_dotenv

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import openai

class SimpleChatbotTester:
    """Simplified chatbot tester with token tracking"""
    
    def __init__(self):
        """Initialize the chatbot tester using environment variables"""
        # Load environment variables from .env file
        load_dotenv()
        
        # Get API key from environment
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            print("❌ OPENAI_API_KEY not found in environment variables")
            print("Please check your .env file")
            sys.exit(1)
        self.llm = ChatOpenAI(
            model_name="gpt-5-mini",
            openai_api_key=self.api_key,
            temperature=0.7
        )
        
        # Message history for conversation context
        self.message_history = []
        
        # Token tracking
        self.total_tokens = 0
        self.input_tokens = 0
        self.output_tokens = 0
        
        print("✓ Initialized GPT-5-Mini model")
    
    def load_case_data(self, json_file_path: str) -> Dict[str, Any]:
        """Load case data from breast_feeding.json"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                case_data = json.load(f)
            print(f"📋 Loaded case: {case_data['case_metadata']['case_title']}")
            return case_data
        except FileNotFoundError:
            print(f"✗ File not found: {json_file_path}")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"✗ Invalid JSON format in: {json_file_path}")
            sys.exit(1)
    
    def setup_conversation(self, case_data: Dict[str, Any]) -> str:
        """Set up the conversation with enhanced Thai prompt structure"""
        mother_profile = case_data['simulation_view']['mother_profile']
        simulation_instructions = case_data['simulation_view']['simulation_instructions']
        
        # Extract child information from examiner_view (safe to use for basic demographics)
        examiner_view = case_data.get('examiner_view', {})
        patient_bg = examiner_view.get('patient_background', {})
        child_name = patient_bg.get('child_name', 'ด.ช.ยินดี ปรีดา')
        child_age = patient_bg.get('child_age_days_or_months', '5 วัน')
        
        # Get key information from feeding_and_sleep data
        feeding_sleep = case_data['simulation_view'].get('feeding_and_sleep', {})
        
        # Build natural conversation prompt emphasizing SHORT responses and NO proactive questioning
        system_prompt = f"""คุณคือ {mother_profile.get('name', 'วาสนา ปรีดา')} อายุ {mother_profile.get('age', 25)} ปี แม่ของ{child_name} อายุ {child_age}

== สถานการณ์ ==
{simulation_instructions.get('scenario', 'พาลูกมาตรวจติดตามน้ำหนักและปรึกษาเรื่องการให้นม')}

== ข้อมูลสำคัญที่คุณรู้ ==
- ลูกให้นม: {feeding_sleep.get('feeding_type', 'นมแม่')}
- ความถี่: {feeding_sleep.get('frequency', 'ทุก 3 ชั่วโมง')}
- ระยะเวลา: {feeding_sleep.get('duration_per_feed', '15-20 นาที')}
- สภาพเต้านม: {feeding_sleep.get('maternal_breast_condition', 'หัวนมแตก')}
- การนอน: {feeding_sleep.get('daytime_sleep', '3-4 ชั่วโมง/ครั้ง')}
- การถ่าย: {feeding_sleep.get('stool_pattern', 'สีเหลืองทอง 4-6 ครั้ง/วัน')}
- การปัสสาวะ: {feeding_sleep.get('urine_pattern', 'สีเหลืองใส 6-8 ครั้ง/วัน')}

== วิธีการตอบ (สำคัญมาก!) ==
1. คุณเป็นผู้ป่วย ไม่ใช่หมอ - ห้ามถามคำถามทางการแพทย์
2. รอให้หมอถามก่อน แล้วค่อยตอบสั้นๆ
3. ตอบเฉพาะสิ่งที่ถูกถามเท่านั้น
4. ใช้ "ค่ะ" เสมอ
5. พูดแบบแม่คนไทยทั่วไป ไม่ใช้คำทางการแพทย์
6. แสดงความกังวลแบบธรรมชาติ แต่ไม่ถามคำถามเชิงเทคนิค

== ข้อห้ามสำคัญ ==
× ห้ามถามคำถามใดๆ กลับไปหาหมอ
× ห้ามเสนอแนะให้หมอพูดเรื่องอะไร
× ห้ามถามว่า "มีอะไรอยากทราบไหม" หรือคำถามแนวนี้
× ห้ามทำหน้าที่เป็นผู้นำการสนทนา
× ห้ามบอกข้อมูลทั้งหมดในครั้งเดียว
× ห้ามใช้คำศัพท์การแพทย์ที่ซับซ้อน

จำไว้: คุณเป็นแม่ที่มาพาลูกมาหาหมอ ให้ทำตัวเป็นผู้ป่วยธรรมดา รอให้หมอซักถาม"""
        
        # Add system message to history
        system_message = SystemMessage(content=system_prompt)
        self.message_history = [system_message]
        
        return system_prompt
    
    def chat_turn(self, student_message: str) -> Tuple[str, float]:
        """Process one turn of conversation with token tracking"""
        start_time = time.time()
        
        try:
            # Add student message to history
            human_message = HumanMessage(content=student_message)
            self.message_history.append(human_message)
            
            # Keep last 15 messages to maintain context but avoid too long prompts
            messages_to_send = self.message_history[-15:]
            
            # Generate response
            response = self.llm.generate([messages_to_send])
            
            # Extract token usage information
            if hasattr(response, 'llm_output') and response.llm_output:
                token_usage = response.llm_output.get('token_usage', {})
                if token_usage:
                    self.input_tokens += token_usage.get('prompt_tokens', 0)
                    self.output_tokens += token_usage.get('completion_tokens', 0)
                    self.total_tokens += token_usage.get('total_tokens', 0)
            
            # Get the actual response text
            patient_response = response.generations[0][0].text
            
            # Add AI response to history
            ai_message = AIMessage(content=patient_response)
            self.message_history.append(ai_message)
            
            response_time = time.time() - start_time
            return patient_response, response_time
            
        except Exception as e:
            error_msg = f"ขอโทษค่ะ เกิดข้อผิดพลาด: {str(e)}"
            return error_msg, 0.0
    
    def interactive_chat(self, case_data: Dict[str, Any]):
        """Start interactive chat session"""
        print("\n" + "="*60)
        print("🏥 Thai Medical OSCE Chatbot Test")
        print(f"📝 Case: {case_data['case_metadata']['case_title']}")
        print(f"🤖 Model: GPT-5-Mini")
        print("="*60)
        
        # Setup conversation
        system_prompt = self.setup_conversation(case_data)
        
        mother_profile = case_data['simulation_view']['mother_profile']
        
        print(f"\n📋 Simulation Setup:")
        print(f"👤 Role: {mother_profile['name']} ({mother_profile['role']})")
        print(f"😊 Emotional State: {mother_profile['emotional_state']}")
        
        print(f"\n💬 เริ่มการสนทนา (พิมพ์ 'quit' เพื่อจบ):")
        
        while True:
            try:
                # Get student input
                student_input = input("\n🧑‍⚕️ นักศึกษา: ").strip()
                
                if student_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not student_input:
                    continue
                
                # Generate response
                print("\n🤔 กำลังคิด...", end="", flush=True)
                patient_response, response_time = self.chat_turn(student_input)
                print(f"\r{' ' * 15}\r", end="")  # Clear thinking message
                
                # Show response
                print(f"👩‍⚕️ มารดา: {patient_response}")
                print(f"⏱️  เวลาตอบ: {response_time:.2f}s")
                
            except KeyboardInterrupt:
                print("\n👋 การสนทนาถูกยกเลิก")
                break
            except Exception as e:
                print(f"\n❌ เกิดข้อผิดพลาด: {str(e)}")
        
        # Show final summary
        self.show_session_summary()
    
    def show_session_summary(self):
        """Show session summary with token usage"""
        print("\n" + "="*60)
        print("📊 สรุปการใช้งาน")
        print("="*60)
        
        print(f"🔢 Token Usage:")
        print(f"   📥 Input Tokens: {self.input_tokens:,}")
        print(f"   📤 Output Tokens: {self.output_tokens:,}")
        print(f"   📊 Total Tokens: {self.total_tokens:,}")
        
        # Calculate conversation stats
        total_messages = len([msg for msg in self.message_history if not isinstance(msg, SystemMessage)])
        student_messages = len([msg for msg in self.message_history if isinstance(msg, HumanMessage)])
        patient_responses = len([msg for msg in self.message_history if isinstance(msg, AIMessage)])
        
        print(f"\n💬 Conversation Stats:")
        print(f"   📝 Total Messages: {total_messages}")
        print(f"   🧑‍⚕️ Student Questions: {student_messages}")
        print(f"   👩‍⚕️ Patient Responses: {patient_responses}")
        
        # Estimate cost (official GPT-5-Mini rates)
        input_cost = (self.input_tokens / 1000000) * 0.25  # $0.25 per 1M input tokens
        output_cost = (self.output_tokens / 1000000) * 2.00  # $2.00 per 1M output tokens
        total_cost = input_cost + output_cost
        
        print(f"\n💰 Actual Cost (USD) - GPT-5-Mini:")
        print(f"   📥 Input Cost: ${input_cost:.6f} ($0.25 per 1M tokens)")
        print(f"   📤 Output Cost: ${output_cost:.6f} ($2.00 per 1M tokens)")
        print(f"   💳 Total Cost: ${total_cost:.6f}")

def main():
    """Main function"""
    # Check if breast_feeding.json exists
    json_file_path = "breast_feeding.json"
    if not os.path.exists(json_file_path):
        print(f"❌ File not found: {json_file_path}")
        print("Please make sure breast_feeding.json is in the current directory")
        sys.exit(1)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("Please create a .env file with your OPENAI_API_KEY")
        print("\nExample .env file content:")
        print("OPENAI_API_KEY=your-api-key-here")
        sys.exit(1)
    
    try:
        # Initialize tester (will load environment variables)
        tester = SimpleChatbotTester()
        
        # Load case data
        case_data = tester.load_case_data(json_file_path)
        
        # Start interactive chat
        tester.interactive_chat(case_data)
        
    except KeyboardInterrupt:
        print("\n👋 ขอบคุณที่ทดสอบ chatbot!")
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()