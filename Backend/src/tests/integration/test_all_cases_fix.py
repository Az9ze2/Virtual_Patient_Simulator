#!/usr/bin/env python3
"""
Comprehensive test to verify that basic history questions don't trigger
fallback questions in ANY of the available JSON case files.
"""

import json
import os
import sys
import glob
from chatbot_test_script_v0_6 import SimpleChatbotTester

def copy_all_case_files():
    """Copy all case files from Extracted_Data_json to current directory"""
    source_dir = "C:\\Users\\acer\\Desktop\\IRPC_Internship\\Virtual_Patient_Simulator\\Backend\\Extracted_Data_json\\"
    
    if not os.path.exists(source_dir):
        print(f"❌ Source directory not found: {source_dir}")
        return []
    
    # Find all JSON files in source directory
    json_files = glob.glob(os.path.join(source_dir, "*.json"))
    copied_files = []
    
    for source_file in json_files:
        filename = os.path.basename(source_file)
        dest_file = filename
        
        # Copy if not already exists
        if not os.path.exists(dest_file):
            try:
                import shutil
                shutil.copy2(source_file, dest_file)
                print(f"📂 Copied: {filename}")
                copied_files.append(filename)
            except Exception as e:
                print(f"⚠️ Failed to copy {filename}: {e}")
        else:
            copied_files.append(filename)
    
    return copied_files

def test_case_file(case_file):
    """Test a single case file with basic history questions"""
    
    # The problematic basic history questions that should NOT trigger fallback questions
    basic_history_questions = [
        "อาการเป็นมาตั้งแต่เมื่อไหร่ครับ",    # How long have symptoms been present?
        "มีอาการอื่นร่วมด้วยไหมครับ",        # Are there other symptoms?  
        "เคยไปหาหมอมาก่อนไหมครับ",         # Have you seen a doctor before?
        "น้องชื่ออะไรครับ อายุเท่าไหร่",      # What's the child's name and age?
        "มีประวัติแพ้ยาหรือไม่ครับ"          # Any drug allergies?
    ]
    
    try:
        # Initialize chatbot
        bot = SimpleChatbotTester(memory_mode="truncate", model_choice="gpt-4.1-mini")
        case_data = bot.load_case_data(case_file)
        bot.setup_conversation(case_data)
        
        # Get case info
        case_title = case_data.get('case_info', {}).get('title', 'Unknown')
        fallback_questions = [q['simulator_ask'] for q in bot.questions_to_ask]
        
        result = {
            'case_file': case_file,
            'case_title': case_title[:80] + "..." if len(case_title) > 80 else case_title,
            'fallback_questions_count': len(fallback_questions),
            'fallback_questions': fallback_questions,
            'tests': [],
            'total_false_positives': 0
        }
        
        # Test each basic history question
        for question in basic_history_questions:
            # Reset fallback questions status
            for q in bot.questions_to_ask:
                q['asked'] = False
            
            # Get status before
            questions_before = [(q['simulator_ask'], q['asked']) for q in bot.questions_to_ask]
            
            try:
                # Send the test question
                response, time_taken = bot.chat_turn(question)
                
                # Get status after  
                questions_after = [(q['simulator_ask'], q['asked']) for q in bot.questions_to_ask]
                
                # Check for false positives (questions marked as asked when they shouldn't be)
                false_positives = []
                for (q_before, asked_before), (q_after, asked_after) in zip(questions_before, questions_after):
                    if not asked_before and asked_after:
                        false_positives.append(q_after)
                
                test_result = {
                    'question': question,
                    'false_positives': false_positives,
                    'response_preview': response[:100] + "..." if len(response) > 100 else response
                }
                
                result['tests'].append(test_result)
                result['total_false_positives'] += len(false_positives)
                
            except Exception as e:
                result['tests'].append({
                    'question': question,
                    'error': str(e),
                    'false_positives': []
                })
        
        return result
        
    except Exception as e:
        return {
            'case_file': case_file,
            'case_title': 'ERROR',
            'error': str(e),
            'fallback_questions_count': 0,
            'fallback_questions': [],
            'tests': [],
            'total_false_positives': 0
        }

def main():
    print("🚀 COMPREHENSIVE TEST: All Case Files - Fallback Question Fix Verification")
    print("=" * 80)
    
    # Copy all case files
    print("📂 Copying case files...")
    available_files = copy_all_case_files()
    
    if not available_files:
        print("❌ No case files found to test!")
        return
    
    # Filter for JSON files that exist locally
    json_files = [f for f in available_files if f.endswith('.json') and os.path.exists(f)]
    
    print(f"📋 Found {len(json_files)} case files to test")
    print("-" * 80)
    
    # Test results storage
    all_results = []
    total_cases_tested = 0
    cases_with_fallbacks = 0
    cases_with_false_positives = 0
    total_false_positives = 0
    
    # Test each case file
    for i, case_file in enumerate(json_files, 1):
        print(f"\n🧪 Testing {i}/{len(json_files)}: {case_file}")
        
        result = test_case_file(case_file)
        all_results.append(result)
        total_cases_tested += 1
        
        if result.get('error'):
            print(f"   ❌ ERROR: {result['error']}")
            continue
            
        if result['fallback_questions_count'] > 0:
            cases_with_fallbacks += 1
            print(f"   📝 Fallback questions: {result['fallback_questions_count']}")
            
            if result['total_false_positives'] > 0:
                cases_with_false_positives += 1
                total_false_positives += result['total_false_positives']
                print(f"   ⚠️  FALSE POSITIVES: {result['total_false_positives']}")
                
                # Show details for problematic cases
                for test in result['tests']:
                    if test.get('false_positives'):
                        print(f"      Question: \"{test['question']}\"")
                        for fp in test['false_positives']:
                            print(f"        -> Triggered: {fp[:60]}...")
            else:
                print(f"   ✅ GOOD: No false positives detected")
        else:
            print(f"   ℹ️  No fallback questions in this case")
    
    # Final summary
    print("\n" + "=" * 80)
    print("📊 FINAL RESULTS SUMMARY")
    print("=" * 80)
    print(f"📋 Total cases tested: {total_cases_tested}")
    print(f"📝 Cases with fallback questions: {cases_with_fallbacks}")
    print(f"❌ Cases with false positives: {cases_with_false_positives}")
    print(f"🔢 Total false positives found: {total_false_positives}")
    
    if cases_with_false_positives == 0:
        print("\n🎉 SUCCESS: No false positives detected across all cases!")
        print("✅ The fix is working correctly for all available test cases.")
    else:
        print(f"\n⚠️ ISSUES FOUND: {cases_with_false_positives} cases still have false positives")
        print("❌ The fix may need further refinement.")
        
        # Show detailed breakdown of problematic cases
        print("\n🔍 PROBLEMATIC CASES:")
        for result in all_results:
            if result.get('total_false_positives', 0) > 0:
                print(f"\n📁 {result['case_file']}:")
                print(f"   Title: {result['case_title']}")
                print(f"   False positives: {result['total_false_positives']}")
                for test in result['tests']:
                    if test.get('false_positives'):
                        print(f"   • \"{test['question']}\" -> {len(test['false_positives'])} triggers")
    
    print("\n" + "=" * 80)
    return cases_with_false_positives == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
