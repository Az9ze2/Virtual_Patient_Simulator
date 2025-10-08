#!/usr/bin/env python3
"""
Test Case 9 with better triggers to ensure both questions get triggered.
"""

from chatbot_test_script_v0_6 import SimpleChatbotTester

def test_case_9_complete():
    """Test Case 9 with better trigger questions for both fallback questions"""
    
    case_file = "01_09_hydrocele.json"
    
    print("🧪 Testing Case 9 Complete: Both Fallback Questions")
    print("=" * 60)
    
    # Initialize bot
    bot = SimpleChatbotTester(memory_mode="truncate", model_choice="gpt-4.1-mini")
    case_data = bot.load_case_data(case_file)
    bot.setup_conversation(case_data)
    
    fallback_questions = [q['simulator_ask'] for q in bot.questions_to_ask]
    print(f"Fallback questions ({len(fallback_questions)}):")
    for i, q in enumerate(fallback_questions, 1):
        print(f"  {i}. {q}")
    print()
    
    # Start conversation
    response1, _ = bot.chat_turn("สวัสดีครับ วันนี้มีเรื่องอะไรให้ช่วยครับ")
    print(f"1. Initial: {response1[:80]}...")
    
    # Test different trigger approaches for the first question (about abnormality)
    print(f"\\n2. Triggering first question (about abnormality)...")
    triggers_1 = [
        "อัณฑะผิดปกติไหม",
        "ลูกปกติไหมครับ", 
        "มีอะไรผิดปกติไหม"
    ]
    
    for trigger in triggers_1:
        print(f"   Trying: \"{trigger}\"")
        response, _ = bot.chat_turn(trigger)
        print(f"   Response: {response[:60]}...")
        
        triggered = sum(1 for q in bot.questions_to_ask if q['asked'])
        print(f"   Total triggered: {triggered}/2")
        
        if triggered > 0:
            break
    
    # Test triggers for second question (about treatment/surgery) 
    print(f"\\n3. Triggering second question (about treatment)...")
    triggers_2 = [
        "รักษายังไงดีครับ",
        "ต้องทำอะไรบ้าง", 
        "จะรักษาอย่างไร"
    ]
    
    initial_triggered = sum(1 for q in bot.questions_to_ask if q['asked'])
    
    for trigger in triggers_2:
        print(f"   Trying: \"{trigger}\"")
        response, _ = bot.chat_turn(trigger)
        print(f"   Response: {response[:60]}...")
        
        triggered = sum(1 for q in bot.questions_to_ask if q['asked'])
        print(f"   Total triggered: {triggered}/2")
        
        if triggered > initial_triggered:
            break
    
    # Check final status
    final_triggered = sum(1 for q in bot.questions_to_ask if q['asked'])
    print(f"\\n4. Final status: {final_triggered}/2 questions triggered")
    
    # Test "no more questions"
    print(f"\\n5. Testing 'no more questions' response...")
    final_response, _ = bot.chat_turn("มีคำถามอะไรอีกมั้ยครับ")
    print(f"   Response: \"{final_response}\"")
    
    # Analyze result
    has_no_more = any(word in final_response.lower() for word in ['ไม่มีคำถาม', 'ไม่มีอะไร', 'ไม่มีแล้ว', 'หมดแล้ว'])
    
    print(f"\\n🎯 ANALYSIS:")
    print(f"   Questions triggered: {final_triggered}/2")
    print(f"   Contains 'no more questions': {has_no_more}")
    
    if final_triggered == 2 and has_no_more:
        print(f"   ✅ SUCCESS: All questions triggered and correct final response")
        return True
    elif final_triggered == 2 and not has_no_more:
        print(f"   ⚠️  PARTIAL: All questions triggered but wrong final response")
        return False
    elif final_triggered < 2 and not has_no_more:
        print(f"   ✅ CORRECT BEHAVIOR: Not all questions triggered, so showing remaining questions")
        return True
    else:
        print(f"   ❌ UNEXPECTED: Mixed results")
        return False

if __name__ == "__main__":
    test_case_9_complete()
