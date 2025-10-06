#!/usr/bin/env python3
"""
Focused test for specific cases with known fallback questions.
Tests the complete workflow: trigger questions -> verify responses -> test "no more questions"
"""

import json
import os
import sys
from chatbot_test_script_v0_6 import SimpleChatbotTester

def test_case_8_gastroenteritis():
    """Test Case 8: Gastroenteritis - Has 1 fallback question"""
    case_file = "01_08_gastroenteritis.json"
    
    print("🧪 Testing Case 8: Gastroenteritis")
    print("=" * 50)
    
    # Initialize bot
    bot = SimpleChatbotTester(memory_mode="truncate", model_choice="gpt-4.1-mini")
    case_data = bot.load_case_data(case_file)
    bot.setup_conversation(case_data)
    
    fallback_questions = [q['simulator_ask'] for q in bot.questions_to_ask]
    print(f"Fallback questions: {fallback_questions}")
    print(f"Question limit: {bot.question_limit_type}")
    
    # Start conversation
    response1, _ = bot.chat_turn("สวัสดีครับ วันนี้มีเรื่องอะไรให้ช่วยครับ")
    print(f"\\n1. Initial greeting response: {response1[:100]}...")
    
    # Test legitimate question that should trigger fallback
    print(f"\\n2. Testing trigger question...")
    response2, _ = bot.chat_turn("ลูกจะเป็นอะไรมากไหม")
    print(f"   Question: \"ลูกจะเป็นอะไรมากไหม\"")
    print(f"   Response: {response2[:100]}...")
    
    # Check if fallback was triggered
    triggered_questions = [q['simulator_ask'] for q in bot.questions_to_ask if q['asked']]
    print(f"   Triggered questions: {len(triggered_questions)}")
    for q in triggered_questions:
        print(f"   - {q}")
    
    # Now test "no more questions"
    print(f"\\n3. Testing 'no more questions' response...")
    final_response, _ = bot.chat_turn("มีคำถามอะไรอีกมั้ยครับ")
    print(f"   Question: \"มีคำถามอะไรอีกมั้ยครับ\"")
    print(f"   Response: \"{final_response}\"")
    
    # Analyze final response
    has_no_more = any(word in final_response.lower() for word in ['ไม่มีคำถาม', 'ไม่มีอะไร', 'ไม่มีแล้ว', 'หมดแล้ว'])
    doesnt_repeat = not any(key_word in final_response for key_word in ['เป็นอะไร', 'มาก', 'รุนแรง'])
    
    print(f"   ✅ Contains 'no more questions': {has_no_more}")
    print(f"   ✅ Doesn't repeat fallback: {doesnt_repeat}")
    
    success = len(triggered_questions) > 0 and has_no_more and doesnt_repeat
    print(f"\\n🎯 RESULT: {'✅ PASSED' if success else '❌ FAILED'}")
    
    return success

def test_case_9_hydrocele():
    """Test Case 9: Hydrocele - Has 2 fallback questions"""
    case_file = "01_09_hydrocele.json"
    
    print("\\n\\n🧪 Testing Case 9: Hydrocele")
    print("=" * 50)
    
    # Initialize bot
    bot = SimpleChatbotTester(memory_mode="truncate", model_choice="gpt-4.1-mini")
    case_data = bot.load_case_data(case_file)
    bot.setup_conversation(case_data)
    
    fallback_questions = [q['simulator_ask'] for q in bot.questions_to_ask]
    print(f"Fallback questions ({len(fallback_questions)}):")
    for i, q in enumerate(fallback_questions, 1):
        print(f"  {i}. {q}")
    print(f"Question limit: {bot.question_limit_type}")
    
    # Start conversation
    response1, _ = bot.chat_turn("สวัสดีครับ วันนี้มีเรื่องอะไรให้ช่วยครับ")
    print(f"\\n1. Initial greeting response: {response1[:100]}...")
    
    # Test trigger questions for different fallback questions
    trigger_questions = [
        "รักษายังไงดีครับ",  # Should trigger treatment-related fallback
        "ต้องผ่าตัดไหม"       # Should trigger surgery-related fallback
    ]
    
    all_triggered = 0
    
    for i, trigger in enumerate(trigger_questions, 2):
        print(f"\\n{i}. Testing trigger question...")
        response, _ = bot.chat_turn(trigger)
        print(f"   Question: \"{trigger}\"")
        print(f"   Response: {response[:100]}...")
        
        # Check newly triggered questions
        newly_triggered = [q['simulator_ask'] for q in bot.questions_to_ask if q['asked']]
        if len(newly_triggered) > all_triggered:
            all_triggered = len(newly_triggered)
            print(f"   ✅ New question triggered!")
            for q in newly_triggered[-1:]:  # Show only the latest
                print(f"   - {q}")
        else:
            print(f"   ➡️ No new questions triggered")
    
    # Test "no more questions" - should only work if all/expected questions are triggered
    print(f"\\n{len(trigger_questions)+2}. Testing 'no more questions' response...")
    final_response, _ = bot.chat_turn("มีคำถามอะไรอีกมั้ยครับ")
    print(f"   Question: \"มีคำถามอะไรอีกมั้ยครับ\"")
    print(f"   Response: \"{final_response}\"")
    
    # Analyze final response
    has_no_more = any(word in final_response.lower() for word in ['ไม่มีคำถาม', 'ไม่มีอะไร', 'ไม่มีแล้ว', 'หมดแล้ว'])
    
    # Check if it doesn't repeat key words from fallback questions
    key_words_to_avoid = ['รักษา', 'ผ่าตัด', 'ทำ', 'อัณฑะ']
    doesnt_repeat = not any(key_word in final_response for key_word in key_words_to_avoid)
    
    print(f"   ✅ Contains 'no more questions': {has_no_more}")
    print(f"   ✅ Doesn't repeat fallback content: {doesnt_repeat}")
    print(f"   📊 Total questions triggered: {all_triggered}/{len(fallback_questions)}")
    
    success = all_triggered > 0 and has_no_more and doesnt_repeat
    print(f"\\n🎯 RESULT: {'✅ PASSED' if success else '❌ FAILED'}")
    
    return success

def test_case_10_iron_deficiency():
    """Test Case 10: Iron Deficiency - Has 4 fallback questions"""
    case_file = "01_10_iron_def-ข้อสอบ_ฝึก_SP.json"
    
    print("\\n\\n🧪 Testing Case 10: Iron Deficiency")
    print("=" * 50)
    
    # Initialize bot
    bot = SimpleChatbotTester(memory_mode="truncate", model_choice="gpt-4.1-mini")
    case_data = bot.load_case_data(case_file)
    bot.setup_conversation(case_data)
    
    fallback_questions = [q['simulator_ask'] for q in bot.questions_to_ask]
    print(f"Fallback questions ({len(fallback_questions)}):")
    for i, q in enumerate(fallback_questions, 1):
        print(f"  {i}. {q}")
    print(f"Question limit: {bot.question_limit_type}")
    
    # Start conversation
    response1, _ = bot.chat_turn("สวัสดีครับ วันนี้มีเรื่องอะไรให้ช่วยครับ")
    print(f"\\n1. Initial greeting response: {response1[:100]}...")
    
    # Test trigger questions for different types of fallbacks
    trigger_questions = [
        "ลูกเป็นอะไรมากไหม",        # Severity/condition
        "ต้องตรวจอะไรเพิ่มเติมไหม", # Additional tests
        "ต้องนอนโรงพยาบาลไหม",     # Hospitalization
        "ต้องกินยานานแค่ไหน"       # Medication duration
    ]
    
    triggered_count = 0
    
    for i, trigger in enumerate(trigger_questions, 2):
        print(f"\\n{i}. Testing trigger question {i-1}...")
        response, _ = bot.chat_turn(trigger)
        print(f"   Question: \"{trigger}\"")
        print(f"   Response: {response[:100]}...")
        
        # Count triggered questions
        current_triggered = sum(1 for q in bot.questions_to_ask if q['asked'])
        if current_triggered > triggered_count:
            triggered_count = current_triggered
            print(f"   ✅ Question(s) triggered! Total: {triggered_count}")
        else:
            print(f"   ➡️ No new questions triggered")
    
    # Test "no more questions"
    print(f"\\n{len(trigger_questions)+2}. Testing 'no more questions' response...")
    final_response, _ = bot.chat_turn("มีคำถามอะไรอีกมั้ยครับ")
    print(f"   Question: \"มีคำถามอะไรอีกมั้ยครับ\"")
    print(f"   Response: \"{final_response}\"")
    
    # Analyze final response
    has_no_more = any(word in final_response.lower() for word in ['ไม่มีคำถาม', 'ไม่มีอะไร', 'ไม่มีแล้ว', 'หมดแล้ว'])
    
    # Avoid repeating key fallback content
    key_words_to_avoid = ['ตรวจ', 'โรงพยาบาล', 'ธาตุเหล็ก', 'กิน', 'นาน']
    doesnt_repeat = not any(key_word in final_response for key_word in key_words_to_avoid)
    
    print(f"   ✅ Contains 'no more questions': {has_no_more}")
    print(f"   ✅ Doesn't repeat fallback content: {doesnt_repeat}")
    print(f"   📊 Total questions triggered: {triggered_count}/{len(fallback_questions)}")
    
    success = triggered_count > 0 and has_no_more and doesnt_repeat
    print(f"\\n🎯 RESULT: {'✅ PASSED' if success else '❌ FAILED'}")
    
    return success

def main():
    print("🧪 FOCUSED FALLBACK FUNCTIONALITY TEST")
    print("=" * 80)
    print("Testing specific cases with known fallback questions:")
    print("1. Legitimate questions trigger fallback questions")
    print("2. 'No more questions' response works correctly")
    print("3. System doesn't repeat already-asked questions")
    print("=" * 80)
    
    # Test specific cases
    results = []
    
    # Test Case 8
    if os.path.exists("01_08_gastroenteritis.json"):
        results.append(test_case_8_gastroenteritis())
    else:
        print("⚠️ Case 8 file not found")
        results.append(False)
    
    # Test Case 9  
    if os.path.exists("01_09_hydrocele.json"):
        results.append(test_case_9_hydrocele())
    else:
        print("⚠️ Case 9 file not found")
        results.append(False)
    
    # Test Case 10
    if os.path.exists("01_10_iron_def-ข้อสอบ_ฝึก_SP.json"):
        results.append(test_case_10_iron_deficiency())
    else:
        print("⚠️ Case 10 file not found")
        results.append(False)
    
    # Final summary
    passed = sum(results)
    total = len(results)
    
    print("\\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    print(f"📋 Cases tested: {total}")
    print(f"✅ Cases passed: {passed}")
    print(f"❌ Cases failed: {total - passed}")
    print(f"📈 Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\\n🎉 SUCCESS: All fallback functionality tests passed!")
        print("✅ The system correctly:")
        print("   - Triggers fallback questions for legitimate inputs")
        print("   - Responds with 'no more questions' when appropriate")
        print("   - Doesn't repeat already-asked questions")
    else:
        print("\\n⚠️ Some tests failed - see details above")
    
    print("=" * 80)
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
