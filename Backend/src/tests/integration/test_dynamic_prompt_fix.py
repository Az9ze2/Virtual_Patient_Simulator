#!/usr/bin/env python3
"""
Test script to verify the dynamic system prompt fix
"""

import os
import sys
import importlib.util

# Import the chatbot module
spec = importlib.util.spec_from_file_location("chatbot_test_script_v0_6", "chatbot_test_script_v0.6.py")
chatbot_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chatbot_module)
SimpleChatbotTester = chatbot_module.SimpleChatbotTester

def test_dynamic_prompt_fix():
    """Test that the AI stops asking questions once they're marked as asked"""
    
    print("🧪 Testing Dynamic System Prompt Fix")
    print("=" * 60)
    
    # Initialize chatbot
    bot = SimpleChatbotTester(memory_mode="summarize", model_choice="gpt-4.1-mini")
    
    # Load case data
    case_file = "01_01_breast_feeding_problems.json"
    if not os.path.exists(case_file):
        print(f"❌ Missing case file: {case_file}")
        return
        
    case_data = bot.load_case_data(case_file)
    bot.setup_conversation(case_data)
    
    print(f"\n📋 Initial setup:")
    print(f"   Questions loaded: {len(bot.questions_to_ask)}")
    for i, q in enumerate(bot.questions_to_ask, 1):
        print(f"      {i}. {q['simulator_ask']} (asked={q['asked']})")
    
    def show_system_prompt_questions(step_name):
        """Helper to show what questions are in the current system prompt"""
        for msg in bot.message_history:
            if hasattr(msg, 'content') and "รายการคำถาม" in msg.content:
                lines = msg.content.split('\n')
                in_question_section = False
                questions_in_prompt = []
                
                for line in lines:
                    if "รายการคำถาม (ถามเฉพาะ asked=False):" in line:
                        in_question_section = True
                        continue
                    elif in_question_section and line.startswith("#"):
                        break
                    elif in_question_section and line.strip().startswith("-"):
                        questions_in_prompt.append(line.strip())
                
                print(f"   📜 {step_name} - Questions in system prompt:")
                if questions_in_prompt:
                    for q in questions_in_prompt:
                        print(f"      {q}")
                else:
                    print("      [ไม่มีคำถามเพิ่มเติม - ผู้เข้าสอบได้ครอบคลุมทุกหัวข้อแล้ว]")
                break
    
    # Test scenario: Progressively ask about each topic
    test_scenarios = [
        {
            "input": "น้ำหนักของลูกเป็นอย่างไรครับ",
            "description": "Ask about weight",
            "expected_marked": "น้ำหนักทารกอยู่ในเกณฑ์ปกติหรือไม่"
        },
        {
            "input": "วิธีการเข้าเต้าเป็นอย่างไรครับ", 
            "description": "Ask about breastfeeding technique",
            "expected_marked": "วิธีการเข้าเต้าถูกต้องหรือไม่และต้องแก้ไขอย่างไร"
        },
        {
            "input": "การดูแลหัวนมแตกต้องทำอย่างไรครับ",
            "description": "Ask about nipple care", 
            "expected_marked": "ต้องดูแลรักษาภาวะหัวนมข้างขวาแตกอย่างไร"
        },
        {
            "input": "มีอะไรอยากถามเพิ่มเติมไหมครับ",
            "description": "Final question - should show no more questions",
            "expected_marked": None
        }
    ]
    
    show_system_prompt_questions("Initial state")
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🧪 Step {i}: {scenario['description']}")
        print(f"   Input: \"{scenario['input']}\"")
        
        # Show status before
        asked_before = sum(1 for q in bot.questions_to_ask if q['asked'])
        print(f"   📊 Before: {asked_before}/{len(bot.questions_to_ask)} questions marked as asked")
        
        # Process the input
        response, time_taken = bot.chat_turn(scenario['input'])
        
        # Show status after
        asked_after = sum(1 for q in bot.questions_to_ask if q['asked']) 
        print(f"   📊 After: {asked_after}/{len(bot.questions_to_ask)} questions marked as asked")
        print(f"   👩‍⚕️ Response: {response}")
        print(f"   ⏱️ Time: {time_taken:.2f}s")
        
        # Show system prompt state
        show_system_prompt_questions(f"Step {i}")
        
        # Check if expected question was marked
        if scenario['expected_marked']:
            marked = any(q['asked'] and scenario['expected_marked'] in q['simulator_ask'] 
                        for q in bot.questions_to_ask)
            print(f"   ✅ Expected question marked: {marked}")
        
        print("-" * 40)
    
    # Final summary
    print(f"\n📊 Final Summary:")
    print(f"   Total questions: {len(bot.questions_to_ask)}")
    print(f"   Questions marked as asked: {sum(1 for q in bot.questions_to_ask if q['asked'])}")
    print(f"   Questions remaining: {sum(1 for q in bot.questions_to_ask if not q['asked'])}")
    
    # Show final question states
    print(f"\n📝 Final question states:")
    for q in bot.questions_to_ask:
        status = "✅ Asked" if q['asked'] else "❌ Not asked"
        print(f"   - {q['simulator_ask'][:50]}... | {status}")
    
    print("\n✅ Dynamic prompt fix test completed!")

if __name__ == "__main__":
    test_dynamic_prompt_fix()
