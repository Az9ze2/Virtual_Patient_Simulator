#!/usr/bin/env python3
"""
Show complete conversation flow including fallback question triggering
and the final "no more questions" response.
"""

from chatbot_test_script_v0_6 import SimpleChatbotTester

def show_complete_conversation(case_file, case_name):
    """Show complete conversation for a case with fallback questions"""
    
    print(f"🎭 COMPLETE CONVERSATION: {case_name}")
    print("=" * 80)
    
    # Initialize bot
    bot = SimpleChatbotTester(memory_mode="truncate", model_choice="gpt-4.1-mini")
    case_data = bot.load_case_data(case_file)
    bot.setup_conversation(case_data)
    
    fallback_questions = [q['simulator_ask'] for q in bot.questions_to_ask]
    print(f"📋 Fallback Questions ({len(fallback_questions)}):")
    for i, q in enumerate(fallback_questions, 1):
        print(f"   {i}. {q}")
    print(f"📝 Question Limit: {bot.question_limit_type}")
    print()
    
    conversation_log = []
    
    def log_exchange(doctor_input, mother_response, context=""):
        """Log a conversation exchange"""
        conversation_log.append({
            'doctor': doctor_input,
            'mother': mother_response,
            'context': context,
            'triggered_questions': [q['simulator_ask'] for q in bot.questions_to_ask if q['asked']],
            'remaining_questions': [q['simulator_ask'] for q in bot.questions_to_ask if not q['asked']]
        })
    
    # 1. Opening greeting
    print("🏥 CONVERSATION START")
    print("-" * 40)
    
    doctor_greeting = "สวัสดีครับ วันนี้มีเรื่องอะไรให้ช่วยครับ"
    mother_response, _ = bot.chat_turn(doctor_greeting)
    log_exchange(doctor_greeting, mother_response, "Opening greeting")
    
    print(f"👨‍⚕️ Doctor: {doctor_greeting}")
    print(f"👩 Mother: {mother_response}")
    print()
    
    # 2. Basic history questions (should NOT trigger fallbacks)
    basic_questions = [
        "น้องชื่ออะไรครับ อายุเท่าไหร่",
        "อาการเป็นมาตั้งแต่เมื่อไหร่ครับ", 
        "มีอาการอื่นร่วมด้วยไหมครับ"
    ]
    
    print("📚 BASIC HISTORY TAKING (Should NOT trigger fallbacks)")
    print("-" * 40)
    
    for question in basic_questions:
        response, _ = bot.chat_turn(question)
        log_exchange(question, response, "Basic history - no fallback expected")
        
        print(f"👨‍⚕️ Doctor: {question}")
        print(f"👩 Mother: {response}")
        
        # Check if any fallbacks were incorrectly triggered
        triggered_count = sum(1 for q in bot.questions_to_ask if q['asked'])
        if triggered_count > 0:
            print(f"   ⚠️  UNEXPECTED: {triggered_count} fallback(s) triggered!")
        else:
            print(f"   ✅ GOOD: No fallbacks triggered")
        print()
    
    # 3. Trigger fallback questions with appropriate medical questions
    print("🎯 TRIGGERING FALLBACK QUESTIONS")
    print("-" * 40)
    
    # Define appropriate triggers for different types of fallback questions
    if case_file == "01_08_gastroenteritis.json":
        trigger_questions = [
            ("ลูกจะเป็นอะไรมากไหม", "Asking about severity/prognosis")
        ]
    elif case_file == "01_09_hydrocele.json":
        trigger_questions = [
            ("อัณฑะผิดปกติไหม", "Asking about abnormality"),
            ("รักษายังไงดีครับ", "Asking about treatment")
        ]
    elif case_file == "01_10_iron_def-ข้อสอบ_ฝึก_SP.json":
        trigger_questions = [
            ("ลูกเป็นอะไรครับ ซีดจากอะไร", "Asking about condition"),
            ("ต้องตรวจอะไรเพิ่มเติมไหม", "Asking about additional tests"),
            ("ต้องนอนโรงพยาบาลไหม", "Asking about hospitalization"),
            ("ต้องกินยานานแค่ไหน", "Asking about medication duration")
        ]
    else:
        trigger_questions = [
            ("มีอะไรที่ควรเป็นห่วงไหม", "General concern question")
        ]
    
    initial_triggered = sum(1 for q in bot.questions_to_ask if q['asked'])
    
    for trigger_question, description in trigger_questions:
        print(f"🎯 {description}")
        response, _ = bot.chat_turn(trigger_question)
        log_exchange(trigger_question, response, f"Trigger: {description}")
        
        print(f"👨‍⚕️ Doctor: {trigger_question}")
        print(f"👩 Mother: {response}")
        
        # Check what was triggered
        current_triggered = sum(1 for q in bot.questions_to_ask if q['asked'])
        newly_triggered = current_triggered - initial_triggered
        
        if newly_triggered > 0:
            print(f"   ✅ SUCCESS: {newly_triggered} new fallback question(s) triggered!")
            # Show which questions were triggered
            triggered_questions = [q['simulator_ask'] for q in bot.questions_to_ask if q['asked']]
            for tq in triggered_questions[-newly_triggered:]:
                print(f"      - {tq}")
        else:
            print(f"   ➡️ No new fallbacks triggered")
        
        initial_triggered = current_triggered
        print()
    
    # 4. Check current status
    final_triggered = sum(1 for q in bot.questions_to_ask if q['asked'])
    remaining = len(fallback_questions) - final_triggered
    
    print("📊 CURRENT STATUS")
    print("-" * 40)
    print(f"Total fallback questions: {len(fallback_questions)}")
    print(f"Questions triggered: {final_triggered}")
    print(f"Questions remaining: {remaining}")
    
    if remaining > 0:
        print("Remaining questions:")
        for q in bot.questions_to_ask:
            if not q['asked']:
                print(f"   - {q['simulator_ask']}")
    print()
    
    # 5. Test "มีคำถามอะไรอีกมั้ยครับ"
    print("🔚 FINAL TEST: 'มีคำถามอะไรอีกมั้ยครับ'")
    print("-" * 40)
    
    final_question = "มีคำถามอะไรอีกมั้ยครับ"
    final_response, _ = bot.chat_turn(final_question)
    log_exchange(final_question, final_response, "Final 'no more questions' test")
    
    print(f"👨‍⚕️ Doctor: {final_question}")
    print(f"👩 Mother: {final_response}")
    print()
    
    # 6. Analyze the final response
    print("🔍 FINAL RESPONSE ANALYSIS")
    print("-" * 40)
    
    has_no_more = any(word in final_response.lower() for word in ['ไม่มีคำถาม', 'ไม่มีอะไร', 'ไม่มีแล้ว', 'หมดแล้ว'])
    
    print(f"Response: \"{final_response}\"")
    print(f"Contains 'no more questions' indicator: {has_no_more}")
    print(f"All fallback questions triggered: {remaining == 0}")
    
    if remaining == 0 and has_no_more:
        print("✅ PERFECT: All questions addressed, correct 'no more questions' response")
    elif remaining == 0 and not has_no_more:
        print("❌ ISSUE: All questions addressed but didn't say 'no more questions'")
    elif remaining > 0 and not has_no_more:
        print("✅ CORRECT: Still has remaining questions, so asking them instead")
    else:
        print("⚠️ UNEXPECTED: Has remaining questions but said 'no more questions'")
    
    print()
    print("=" * 80)
    return conversation_log

def main():
    """Show conversations for different cases"""
    
    test_cases = [
        ("01_08_gastroenteritis.json", "Case 8: Gastroenteritis (1 fallback)"),
        ("01_09_hydrocele.json", "Case 9: Hydrocele (2 fallbacks)"),
        ("01_10_iron_def-ข้อสอบ_ฝึก_SP.json", "Case 10: Iron Deficiency (4 fallbacks)")
    ]
    
    for case_file, case_name in test_cases:
        if not os.path.exists(case_file):
            print(f"⚠️ {case_file} not found, skipping...")
            continue
            
        conversation_log = show_complete_conversation(case_file, case_name)
        
        # Add some spacing between cases
        print("\n" + "🔄" * 80 + "\n")
        
        # Ask user if they want to continue to next case
        try:
            user_input = input("Press Enter to continue to next case, or 'q' to quit: ").strip().lower()
            if user_input == 'q':
                break
        except KeyboardInterrupt:
            break
    
    print("🎭 Conversation demonstrations completed!")

if __name__ == "__main__":
    import os
    main()
