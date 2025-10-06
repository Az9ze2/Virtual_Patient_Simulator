#!/usr/bin/env python3
"""
Debug script to check how the system prompt gets updated when fallback questions are marked as asked.
"""

import json
import os
from chatbot_test_script_v0_6 import SimpleChatbotTester

def debug_system_prompt_updates():
    """Check how system prompt changes as fallback questions are triggered"""
    
    case_file = "01_08_gastroenteritis.json"
    
    print("🔍 DEBUGGING SYSTEM PROMPT UPDATES")
    print("=" * 60)
    
    # Initialize bot
    bot = SimpleChatbotTester(memory_mode="truncate", model_choice="gpt-4.1-mini")
    case_data = bot.load_case_data(case_file)
    bot.setup_conversation(case_data)
    
    fallback_questions = [q['simulator_ask'] for q in bot.questions_to_ask]
    print(f"Fallback questions: {fallback_questions}")
    
    def show_current_prompt_section():
        """Show the current fallback question section of the system prompt"""
        system_msg = bot.message_history[0]
        lines = system_msg.content.split('\n')
        
        # Find the fallback question section
        in_question_section = False
        question_section_lines = []
        
        for line in lines:
            if "สิ่งที่อยากรู้" in line:
                in_question_section = True
                question_section_lines.append(line)
            elif in_question_section and (line.startswith("#") and "สิ่งที่อยากรู้" not in line):
                break
            elif in_question_section:
                question_section_lines.append(line)
        
        print("   Current system prompt section:")
        for line in question_section_lines:
            print(f"   | {line}")
    
    # Show initial state
    print(f"\n1. INITIAL STATE")
    print(f"   Asked status: {[q['asked'] for q in bot.questions_to_ask]}")
    show_current_prompt_section()
    
    # Start conversation
    print(f"\n2. AFTER GREETING")
    response1, _ = bot.chat_turn("สวัสดีครับ วันนี้มีเรื่องอะไรให้ช่วยครับ")
    print(f"   Response: {response1[:80]}...")
    print(f"   Asked status: {[q['asked'] for q in bot.questions_to_ask]}")
    show_current_prompt_section()
    
    # Trigger fallback question
    print(f"\n3. AFTER TRIGGERING FALLBACK")
    response2, _ = bot.chat_turn("ลูกจะเป็นอะไรมากไหม")
    print(f"   Response: {response2[:80]}...")
    print(f"   Asked status: {[q['asked'] for q in bot.questions_to_ask]}")
    show_current_prompt_section()
    
    # Test "no more questions"
    print(f"\n4. TESTING 'NO MORE QUESTIONS'")
    final_response, _ = bot.chat_turn("มีคำถามอะไรอีกมั้ยครับ")
    print(f"   Response: \"{final_response}\"")
    print(f"   Asked status: {[q['asked'] for q in bot.questions_to_ask]}")
    show_current_prompt_section()
    
    # Analyze the final response
    has_no_more = any(word in final_response.lower() for word in ['ไม่มีคำถาม', 'ไม่มีอะไร', 'ไม่มีแล้ว', 'หมดแล้ว'])
    print(f"\n🎯 ANALYSIS:")
    print(f"   Final response contains 'no more questions': {has_no_more}")
    print(f"   System prompt should show: '[ไม่มีคำถามเพิ่มเติม - ผู้เข้าสอบได้ครอบคลุมทุกหัวข้อแล้ว]'")
    
    if not has_no_more:
        print(f"   ❌ ISSUE: Mother is not following the 'no more questions' instruction")
        print(f"   📝 This suggests the system prompt update logic might need refinement")
    else:
        print(f"   ✅ SUCCESS: Mother is correctly saying no more questions")

if __name__ == "__main__":
    debug_system_prompt_updates()
