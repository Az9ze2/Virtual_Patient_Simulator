#!/usr/bin/env python3
"""
Comprehensive test to verify that:
1. Legitimate questions correctly trigger appropriate fallback questions
2. After all fallback questions are asked, "มีคำถามอะไรอีกมั้ยครับ" gets "ไม่มีคำถามค่ะ" response
3. The system doesn't repeat already-asked fallback questions
"""

import json
import os
import sys
import glob
import re
from chatbot_test_script_v0_6 import SimpleChatbotTester

def find_cases_with_fallbacks():
    """Find all case files that have fallback questions"""
    # Get all JSON files in current directory
    json_files = glob.glob("*.json")
    cases_with_fallbacks = []
    
    for case_file in json_files:
        try:
            bot = SimpleChatbotTester(memory_mode="truncate", model_choice="gpt-4.1-mini")
            case_data = bot.load_case_data(case_file)
            bot.setup_conversation(case_data)
            
            if len(bot.questions_to_ask) > 0:
                cases_with_fallbacks.append({
                    'file': case_file,
                    'title': case_data.get('case_info', {}).get('title', 'Unknown')[:60] + "...",
                    'fallback_count': len(bot.questions_to_ask),
                    'fallback_questions': [q['simulator_ask'] for q in bot.questions_to_ask],
                    'question_limit_type': bot.question_limit_type
                })
        except Exception as e:
            print(f"⚠️ Error processing {case_file}: {e}")
            continue
    
    return cases_with_fallbacks

def create_trigger_questions_for_case(fallback_questions):
    """Create questions that should legitimately trigger each fallback question"""
    trigger_mapping = {}
    
    for i, fallback_q in enumerate(fallback_questions):
        # Analyze fallback question content to create appropriate triggers
        fallback_lower = fallback_q.lower()
        
        if any(word in fallback_lower for word in ['เป็นอะไร', 'รุนแรง', 'อันตราย', 'มาก']):
            # Severity/prognosis questions
            trigger_mapping[i] = [
                "ลูกจะเป็นอะไรมากไหม",
                "อาการนี้รุนแรงมั้ย", 
                "เป็นโรคอะไรครับ"
            ]
        elif any(word in fallback_lower for word in ['รักษา', 'ดูแล', 'ทำ']):
            # Treatment questions
            trigger_mapping[i] = [
                "รักษายังไงดีครับ",
                "ต้องทำอะไรบ้าง",
                "ดูแลยังไงดี"
            ]
        elif any(word in fallback_lower for word in ['ผ่าตัด', 'ผ่าตัด']):
            # Surgery questions  
            trigger_mapping[i] = [
                "ต้องผ่าตัดไหม",
                "ต้องทำศัลยกรรมมั้ย"
            ]
        elif any(word in fallback_lower for word in ['ตรวจ', 'เพิ่มเติม']):
            # Additional tests
            trigger_mapping[i] = [
                "ต้องตรวจอะไรเพิ่มเติมไหม",
                "ต้องส่งตรวจอะไรอีกมั้ย"
            ]
        elif any(word in fallback_lower for word in ['โรงพยาบาล', 'นอน']):
            # Hospitalization
            trigger_mapping[i] = [
                "ต้องนอนโรงพยาบาลไหม",
                "ต้องเข้าไปรักษาไหม"
            ]
        elif any(word in fallback_lower for word in ['พัฒนาการ', 'เดิน', 'ช้า']):
            # Development questions
            trigger_mapping[i] = [
                "พัฒนาการเป็นไง",
                "ลูกเดินได้เมื่อไหร่"
            ]
        elif any(word in fallback_lower for word in ['กิน', 'นาน', 'ธาตุเหล็ก']):
            # Medication duration
            trigger_mapping[i] = [
                "ต้องกินยานานแค่ไหน",
                "ต้องกินธาตุเหล็กนานมั้ย"
            ]
        else:
            # Generic questions
            trigger_mapping[i] = [
                "อยากทราบข้อมูลเพิ่มเติม",
                "มีอะไรที่ต้องสงสัยไหม"
            ]
    
    return trigger_mapping

def test_case_fallback_functionality(case_info):
    """Test a single case's fallback functionality"""
    case_file = case_info['file']
    fallback_questions = case_info['fallback_questions']
    question_limit_type = case_info['question_limit_type']
    
    print(f"\n🧪 Testing: {case_file}")
    print(f"   Title: {case_info['title']}")
    print(f"   Fallback questions: {len(fallback_questions)}")
    print(f"   Limit type: {question_limit_type}")
    
    # Initialize fresh bot
    bot = SimpleChatbotTester(memory_mode="truncate", model_choice="gpt-4.1-mini")
    case_data = bot.load_case_data(case_file)
    bot.setup_conversation(case_data)
    
    # Create appropriate trigger questions
    trigger_mapping = create_trigger_questions_for_case(fallback_questions)
    
    result = {
        'case_file': case_file,
        'fallback_questions': fallback_questions,
        'question_limit_type': question_limit_type,
        'tests': [],
        'all_triggered': True,
        'final_test_passed': False,
        'final_response': ""
    }
    
    # Test each fallback question
    questions_to_test = range(len(fallback_questions))
    if question_limit_type == "single":
        # For single limit, only test the first question
        questions_to_test = [0]
        print(f"   ℹ️ Single question limit - testing only first question")
    
    triggered_count = 0
    
    for idx in questions_to_test:
        fallback_q = fallback_questions[idx]
        triggers = trigger_mapping.get(idx, ["อยากทราบข้อมูลเพิ่มเติม"])
        
        print(f"\n   🎯 Testing fallback {idx+1}: \"{fallback_q[:50]}...\"")
        
        # Try each trigger until one works or all fail
        question_triggered = False
        
        for trigger in triggers:
            # Check if question is already marked as asked
            if idx < len(bot.questions_to_ask) and bot.questions_to_ask[idx]['asked']:
                print(f"      ✅ Already triggered by previous question")
                question_triggered = True
                triggered_count += 1
                break
            
            print(f"      Trying: \"{trigger}\"")
            
            # Send trigger question
            response, time_taken = bot.chat_turn(trigger)
            
            # Check if this fallback question was triggered
            if idx < len(bot.questions_to_ask) and bot.questions_to_ask[idx]['asked']:
                print(f"      ✅ SUCCESS: Fallback question triggered")
                print(f"      Response: {response[:100]}...")
                question_triggered = True
                triggered_count += 1
                break
            else:
                print(f"      ➡️ No trigger, trying next...")
        
        if not question_triggered:
            print(f"      ❌ FAILED: Could not trigger this fallback question")
            result['all_triggered'] = False
        
        result['tests'].append({
            'fallback_question': fallback_q,
            'triggered': question_triggered
        })
    
    # Now test the "no more questions" functionality
    print(f"\n   🔍 Testing final 'no more questions' response...")
    print(f"   Questions triggered: {triggered_count}/{len(questions_to_test)}")
    
    if triggered_count == len(questions_to_test):  # All expected questions were triggered
        final_response, _ = bot.chat_turn("มีคำถามอะไรอีกมั้ยครับ")
        result['final_response'] = final_response
        
        # Check if response indicates no more questions
        no_more_indicators = [
            'ไม่มีคำถาม',
            'ไม่มีอะไรถาม', 
            'ไม่มีอะไรเพิ่มเติม',
            'ไม่มีแล้ว',
            'หมดแล้ว'
        ]
        
        response_lower = final_response.lower()
        has_no_more_indicator = any(indicator.lower() in response_lower for indicator in no_more_indicators)
        
        # Check if response doesn't repeat any of the original fallback questions
        doesnt_repeat_questions = True
        repeated_questions = []
        
        for fallback_q in fallback_questions:
            # Extract key words from fallback question (ignore common words)
            key_words = []
            for word in fallback_q.split():
                if len(word) > 3 and word not in ['ครับ', 'คะ', 'ค่ะ', 'หรือ', 'ไหม', 'มั้ย', 'แล้ว', 'อะไร']:
                    key_words.append(word)
            
            # Check if any key words appear in final response
            if any(key_word in final_response for key_word in key_words):
                doesnt_repeat_questions = False
                repeated_questions.append(fallback_q[:30] + "...")
        
        result['final_test_passed'] = has_no_more_indicator and doesnt_repeat_questions
        
        print(f"   Response: \"{final_response}\"")
        
        if has_no_more_indicator:
            print(f"   ✅ Contains 'no more questions' indicator")
        else:
            print(f"   ❌ Missing 'no more questions' indicator")
        
        if doesnt_repeat_questions:
            print(f"   ✅ Doesn't repeat original fallback questions")
        else:
            print(f"   ❌ Repeats questions: {repeated_questions}")
        
        if result['final_test_passed']:
            print(f"   🎉 FINAL TEST PASSED")
        else:
            print(f"   ❌ FINAL TEST FAILED")
    else:
        print(f"   ⚠️ Skipping final test - not all fallback questions were triggered")
        result['final_test_passed'] = False
    
    return result

def main():
    print("🧪 COMPREHENSIVE FALLBACK FUNCTIONALITY TEST")
    print("=" * 80)
    print("Testing:")
    print("1. Legitimate questions trigger appropriate fallback questions")
    print("2. After all fallbacks are addressed, 'no more questions' response works")
    print("3. System doesn't repeat already-asked fallback questions")
    print("-" * 80)
    
    # Find cases with fallback questions
    cases_with_fallbacks = find_cases_with_fallbacks()
    
    if not cases_with_fallbacks:
        print("❌ No cases with fallback questions found!")
        return False
    
    print(f"📋 Found {len(cases_with_fallbacks)} cases with fallback questions")
    
    # Test each case
    all_results = []
    total_cases = len(cases_with_fallbacks)
    passed_cases = 0
    
    for i, case_info in enumerate(cases_with_fallbacks, 1):
        print(f"\n{'='*60}")
        print(f"CASE {i}/{total_cases}")
        print(f"{'='*60}")
        
        result = test_case_fallback_functionality(case_info)
        all_results.append(result)
        
        if result['all_triggered'] and result['final_test_passed']:
            passed_cases += 1
            print(f"\n🎉 CASE PASSED: All fallback functionality working correctly")
        else:
            print(f"\n❌ CASE FAILED:")
            if not result['all_triggered']:
                print(f"   - Not all fallback questions could be triggered")
            if not result['final_test_passed']:
                print(f"   - Final 'no more questions' test failed")
    
    # Final summary
    print(f"\n{'='*80}")
    print("📊 FINAL RESULTS SUMMARY")
    print(f"{'='*80}")
    print(f"📋 Total cases tested: {total_cases}")
    print(f"✅ Cases passed: {passed_cases}")
    print(f"❌ Cases failed: {total_cases - passed_cases}")
    print(f"📈 Success rate: {passed_cases/total_cases*100:.1f}%")
    
    if passed_cases == total_cases:
        print(f"\n🎉 SUCCESS: All fallback functionality tests passed!")
        print(f"✅ The fallback question system is working correctly.")
    else:
        print(f"\n⚠️ Some cases failed - see details above")
    
    print(f"\n{'='*80}")
    return passed_cases == total_cases

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
