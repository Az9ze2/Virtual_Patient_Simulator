#!/usr/bin/env python3
"""
Debug script to demonstrate how GPT-4 is incorrectly analyzing basic medical questions
as related to fallback questions due to semantic similarity.
"""

import json
import os
from openai import OpenAI

def load_api_key():
    """Load OpenAI API key from environment or file"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        try:
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("OPENAI_API_KEY="):
                        api_key = line.split("=", 1)[1].strip()
                        break
        except FileNotFoundError:
            print("❌ No API key found. Set OPENAI_API_KEY environment variable or create .env file")
            return None
    return api_key

def analyze_question_matching(client, student_input, fallback_questions):
    """
    Use the same analysis logic as _update_question_status to show how GPT-4
    interprets basic medical questions
    """
    # Build numbered question list (same as in _update_question_status)
    questions_list = "\n".join([f"{i+1}. {q}" for i, q in enumerate(fallback_questions)])

    # Same analysis prompt as in the chatbot
    analysis_prompt = [
        {"role": "system", "content": (
            "คุณเป็นผู้เชี่ยวชาญวิเคราะห์การสนทนาทางการแพทย์ "
            "วิเคราะห์ว่าแพทย์ได้ถามหรือกล่าวถึงหัวข้อใดบ้างในรายการคำถาม "
            "ให้พิจารณาทั้งความหมายโดยตรงและความหมายโดยนัย เช่น:\n"
            "- 'น้ำหนักเป็นอย่างไร' = ถามเรื่องน้ำหนัก\n"
            "- 'การให้นมเป็นยังไง' = ถามเรื่องวิธีการให้นม\n"
            "- 'หัวนมแตกต้องดูแลยังไง' = ถามเรื่องการดูแลหัวนมแตก\n"
            "ตอบเป็น JSON array ของหมายเลข เช่น [1, 3] หรือ [] ถ้าไม่มี"
        )},
        {"role": "user", "content": f"""
            แพทย์พูด: "{student_input}"

            รายการคำถาม:
            {questions_list}

            หมายเลขข้อที่แพทย์ได้ถามหรือกล่าวถึงแล้ว:"""}]

    try:
        response = client.chat.completions.create(
            messages=analysis_prompt,
            model="gpt-4.1-mini",
            temperature=0.1,
            max_completion_tokens=50
        )
        raw_output = response.choices[0].message.content.strip()
        
        # Parse the JSON response
        matched_indices = json.loads(raw_output)
        return matched_indices, raw_output
    except Exception as e:
        return None, f"Error: {e}"

def main():
    # Test cases from the problematic scenarios
    test_cases = [
        {
            "case_name": "Case 8 - Gastroenteritis",
            "student_inputs": [
                "อาการเป็นมาตั้งแต่เมื่อไหร่ครับ",
                "มีอาการอื่นร่วมด้วยไหมครับ", 
                "เคยไปหาหมอมาก่อนไหมครับ"
            ],
            "fallback_questions": ["ลูกจะเป็นอะไรมากมั๊ยคะ"]
        },
        {
            "case_name": "Case 9 - Hydrocele", 
            "student_inputs": [
                "อาการเป็นมาตั้งแต่เมื่อไหร่ครับ",
                "มีอาการอื่นร่วมด้วยไหมครับ"
            ],
            "fallback_questions": ["รักษายังไงคะ", "ต้องผ่าตัดมั้ยคะ"]
        },
        {
            "case_name": "Case 10 - Late walking",
            "student_inputs": [
                "อาการเป็นมาตั้งแต่เมื่อไหร่ครับ",
                "มีอาการอื่นร่วมด้วยไหมครับ"
            ],
            "fallback_questions": ["พัฒนาการของลูกเป็นอย่างไรคะ", "ลูกจะเดินได้เมื่อไหร่คะ"]
        }
    ]

    # Load API key
    api_key = load_api_key()
    if not api_key:
        return

    client = OpenAI(api_key=api_key)

    print("🔍 DEBUG: GPT-4 Analysis of Basic Medical Questions vs Fallback Questions")
    print("=" * 80)

    for test_case in test_cases:
        print(f"\n## {test_case['case_name']}")
        print(f"Fallback Questions: {test_case['fallback_questions']}")
        print("-" * 60)

        for student_input in test_case['student_inputs']:
            print(f"\n🧑‍⚕️ Doctor Input: \"{student_input}\"")
            
            matched_indices, raw_response = analyze_question_matching(
                client, student_input, test_case['fallback_questions']
            )
            
            if matched_indices is not None:
                print(f"📊 GPT Response: {raw_response}")
                
                if matched_indices:
                    print("⚠️  PROBLEM: GPT thinks these questions are related:")
                    for idx in matched_indices:
                        if 1 <= idx <= len(test_case['fallback_questions']):
                            print(f"   - Question {idx}: {test_case['fallback_questions'][idx-1]}")
                else:
                    print("✅ Correctly detected no relationship")
            else:
                print(f"❌ Analysis failed: {raw_response}")

    print("\n" + "=" * 80)
    print("🎯 CONCLUSION:")
    print("The GPT analysis is too liberal with 'implied meanings' and considers")
    print("basic history questions as semantically related to specific fallback questions.")
    print("We need to make the analysis prompt more strict and explicit.")

if __name__ == "__main__":
    main()
