#!/usr/bin/env python3
"""
Quick verification that the fix in chatbot_test_script_v0.6.py works correctly
for the problematic Case 8 (Gastroenteritis).
"""

import json
import os
import sys
from chatbot_test_script_v0_6 import SimpleChatbotTester

def test_case_8_fix():
    """Test Case 8 with the basic questions that were causing false positives"""
    
    case_file = "01_08_gastroenteritis.json"
    if not os.path.exists(case_file):
        print(f"❌ Missing case file: {case_file}")
        return False
    
    # Initialize chatbot with the fixed prompt
    bot = SimpleChatbotTester(memory_mode="truncate", model_choice="gpt-4.1-mini")
    case_data = bot.load_case_data(case_file)
    bot.setup_conversation(case_data)
    
    print("🧪 Testing Case 8 (Gastroenteritis) with Fixed GPT Analysis Prompt")
    print("=" * 70)
    print(f"Fallback questions: {[q['simulator_ask'] for q in bot.questions_to_ask]}")
    print()
    
    # Test the problematic inputs
    test_inputs = [
        "อาการเป็นมาตั้งแต่เมื่อไหร่ครับ",
        "มีอาการอื่นร่วมด้วยไหมครับ", 
        "เคยไปหาหมอมาก่อนไหมครับ"
    ]
    
    success_count = 0
    
    for i, test_input in enumerate(test_inputs, 1):
        print(f"Test {i}: \"{test_input}\"")
        
        # Get questions status before
        questions_before = [(q['simulator_ask'][:40] + "...", q['asked']) for q in bot.questions_to_ask]
        
        # Send the test input
        response, time_taken = bot.chat_turn(test_input)
        
        # Get questions status after
        questions_after = [(q['simulator_ask'][:40] + "...", q['asked']) for q in bot.questions_to_ask]
        
        # Check if any fallback questions were incorrectly marked as asked
        changes = []
        for (q_before, asked_before), (q_after, asked_after) in zip(questions_before, questions_after):
            if not asked_before and asked_after:
                changes.append(q_after)
        
        if changes:
            print(f"  ❌ PROBLEM: These fallback questions were incorrectly marked as asked:")
            for change in changes:
                print(f"     - {change}")
            print(f"  Response: {response[:100]}...")
        else:
            print(f"  ✅ GOOD: No fallback questions incorrectly triggered")
            print(f"  Response: {response[:100]}...")
            success_count += 1
        
        print()
    
    print("-" * 70)
    if success_count == len(test_inputs):
        print(f"🎉 SUCCESS: All {len(test_inputs)} tests passed! Fix is working correctly.")
        return True
    else:
        print(f"❌ FAILED: {len(test_inputs) - success_count}/{len(test_inputs)} tests failed.")
        return False

if __name__ == "__main__":
    success = test_case_8_fix()
    sys.exit(0 if success else 1)
