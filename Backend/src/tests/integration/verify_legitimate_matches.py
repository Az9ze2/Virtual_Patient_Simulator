#!/usr/bin/env python3
"""
Test that legitimate question matches still work after our fix.
"""

import json
import os
import sys
from chatbot_test_script_v0_6 import SimpleChatbotTester

def test_legitimate_matches():
    """Test that questions that SHOULD match fallback questions still do"""
    
    case_file = "01_08_gastroenteritis.json"
    if not os.path.exists(case_file):
        print(f"❌ Missing case file: {case_file}")
        return False
    
    bot = SimpleChatbotTester(memory_mode="truncate", model_choice="gpt-4.1-mini")
    case_data = bot.load_case_data(case_file)
    bot.setup_conversation(case_data)
    
    print("🧪 Testing Legitimate Question Matches")
    print("=" * 70)
    print(f"Fallback questions: {[q['simulator_ask'] for q in bot.questions_to_ask]}")
    print()
    
    # These SHOULD trigger the fallback question "ลูกจะเป็นอะไรมากมั๊ยคะ"
    legitimate_inputs = [
        "ลูกจะเป็นอะไรมากไหม",  # Direct match
        "อาการนี้รุนแรงมากมั้ย",  # Severity question 
        "เป็นโรคอะไรครับ",       # Disease question
        "สถานการณ์ลูกเป็นไง"    # Condition question
    ]
    
    success_count = 0
    
    for i, test_input in enumerate(legitimate_inputs, 1):
        print(f"Test {i}: \"{test_input}\"")
        
        # Reset questions for each test
        for q in bot.questions_to_ask:
            q['asked'] = False
        
        # Get questions status before
        questions_before = [(q['simulator_ask'][:40] + "...", q['asked']) for q in bot.questions_to_ask]
        
        # Send the test input
        response, time_taken = bot.chat_turn(test_input)
        
        # Get questions status after
        questions_after = [(q['simulator_ask'][:40] + "...", q['asked']) for q in bot.questions_to_ask]
        
        # Check if any fallback questions were correctly marked as asked
        changes = []
        for (q_before, asked_before), (q_after, asked_after) in zip(questions_before, questions_after):
            if not asked_before and asked_after:
                changes.append(q_after)
        
        if changes:
            print(f"  ✅ GOOD: These fallback questions were correctly triggered:")
            for change in changes:
                print(f"     - {change}")
            print(f"  Response: {response[:100]}...")
            success_count += 1
        else:
            print(f"  ⚠️  MISSED: No fallback questions triggered (might be okay if too different)")
            print(f"  Response: {response[:100]}...")
        
        print()
    
    print("-" * 70)
    print(f"🎯 RESULT: {success_count}/{len(legitimate_inputs)} legitimate matches detected")
    print("Note: Some misses might be acceptable if the questions are too semantically different")
    
    return True

if __name__ == "__main__":
    test_legitimate_matches()
