#!/usr/bin/env python3
"""
Test different improved analysis prompts to fix the false positive issue
with fallback question detection.
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

def analyze_with_original_prompt(client, student_input, fallback_questions):
    """Original analysis prompt (the problematic one)"""
    questions_list = "\n".join([f"{i+1}. {q}" for i, q in enumerate(fallback_questions)])

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
        return json.loads(response.choices[0].message.content.strip())
    except Exception as e:
        return f"Error: {e}"

def analyze_with_improved_prompt_v1(client, student_input, fallback_questions):
    """Improved prompt - more restrictive, requiring direct topic match"""
    questions_list = "\n".join([f"{i+1}. {q}" for i, q in enumerate(fallback_questions)])

    analysis_prompt = [
        {"role": "system", "content": (
            "คุณเป็นผู้เชี่ยวชาญวิเคราะห์การสนทนาทางการแพทย์ "
            "วิเคราะห์ว่าแพทย์ได้ถาม**หัวข้อเดียวกัน**กับคำถามในรายการหรือไม่ "
            "**ห้าม**ตีความเสริมหรือถือว่าเกี่ยวข้องโดยนัย\n\n"
            "กฎการจับคู่:\n"
            "- ต้องเป็นหัวข้อเดียวกันโดยตรง\n"
            "- การถามประวัติทั่วไป (อาการมาเมื่อไหร่, อาการอื่น, เคยพบหมอ) ≠ คำถามเฉพาะเรื่อง\n"
            "- การถามการรักษา ≠ การถามอาการ\n"
            "- การถามพยากรณ์โรค ≠ การถามประวัติ\n\n"
            "ตอบเป็น JSON array ของหมายเลข เช่น [1, 3] หรือ [] ถ้าไม่มี"
        )},
        {"role": "user", "content": f"""
            แพทย์พูด: "{student_input}"

            รายการคำถาม:
            {questions_list}

            หมายเลขข้อที่แพทย์ถาม**หัวข้อเดียวกัน**โดยตรง:"""}]

    try:
        response = client.chat.completions.create(
            messages=analysis_prompt,
            model="gpt-4.1-mini",
            temperature=0.1,
            max_completion_tokens=50
        )
        return json.loads(response.choices[0].message.content.strip())
    except Exception as e:
        return f"Error: {e}"

def analyze_with_improved_prompt_v2(client, student_input, fallback_questions):
    """Improved prompt v2 - even more restrictive with keyword matching"""
    questions_list = "\n".join([f"{i+1}. {q}" for i, q in enumerate(fallback_questions)])

    analysis_prompt = [
        {"role": "system", "content": (
            "วิเคราะห์ว่าแพทย์ถาม**คำถามเดียวกัน**กับรายการหรือไม่\n\n"
            "เงื่อนไขการจับคู่ (ต้องผ่านทั้งหมด):\n"
            "1. หัวข้อหลักต้องเหมือนกัน\n"
            "2. ต้องมีคำสำคัญร่วมกัน\n"
            "3. จุดประสงค์ของการถามต้องเหมือนกัน\n\n"
            "ตัวอย่างที่ **ไม่** ตรงกัน:\n"
            "- 'อาการมาเมื่อไหร่' ≠ 'ลูกจะเป็นอะไรมาก' (ถามเวลา ≠ ถามความรุนแรง)\n"
            "- 'มีอาการอื่นไหม' ≠ 'รักษายังไง' (ถามอาการ ≠ ถามการรักษา)\n"
            "- 'เคยพบหมอ' ≠ 'ต้องผ่าตัดไหม' (ถามประวัติ ≠ ถามการรักษา)\n\n"
            "ตอบเป็น JSON array เช่น [1, 3] หรือ [] ถ้าไม่ตรงข้อใด"
        )},
        {"role": "user", "content": f"""
            แพทย์ถาม: "{student_input}"

            รายการคำถาม:
            {questions_list}

            หมายเลขข้อที่เป็น**คำถามเดียวกัน**:"""}]

    try:
        response = client.chat.completions.create(
            messages=analysis_prompt,
            model="gpt-4.1-mini",
            temperature=0.1,
            max_completion_tokens=50
        )
        return json.loads(response.choices[0].message.content.strip())
    except Exception as e:
        return f"Error: {e}"

def main():
    test_cases = [
        {
            "case_name": "Case 8 - Gastroenteritis (Problematic)",
            "student_inputs": [
                "อาการเป็นมาตั้งแต่เมื่อไหร่ครับ",
                "มีอาการอื่นร่วมด้วยไหมครับ", 
                "เคยไปหาหมอมาก่อนไหมครับ"
            ],
            "fallback_questions": ["ลูกจะเป็นอะไรมากมั๊ยคะ"]
        },
        {
            "case_name": "Legitimate matches (Should still work)",
            "student_inputs": [
                "ลูกจะเป็นอะไรมากไหม",
                "อาการนี้รุนแรงมากมั้ยครับ",
                "รักษายังไงดีครับ",
                "ต้องผ่าตัดไหม"
            ],
            "fallback_questions": ["ลูกจะเป็นอะไรมากมั๊ยคะ", "รักษายังไงคะ", "ต้องผ่าตัดมั้ยคะ"]
        }
    ]

    api_key = load_api_key()
    if not api_key:
        return

    client = OpenAI(api_key=api_key)

    print("🔍 TESTING IMPROVED ANALYSIS PROMPTS")
    print("=" * 80)

    for test_case in test_cases:
        print(f"\n## {test_case['case_name']}")
        print(f"Fallback Questions: {test_case['fallback_questions']}")
        print("-" * 60)

        for student_input in test_case['student_inputs']:
            print(f"\n🧑‍⚕️ Doctor: \"{student_input}\"")
            
            # Test all three approaches
            original = analyze_with_original_prompt(client, student_input, test_case['fallback_questions'])
            improved_v1 = analyze_with_improved_prompt_v1(client, student_input, test_case['fallback_questions'])
            improved_v2 = analyze_with_improved_prompt_v2(client, student_input, test_case['fallback_questions'])
            
            print(f"  📊 Original:     {original}")
            print(f"  🔧 Improved V1:  {improved_v1}")
            print(f"  🔧 Improved V2:  {improved_v2}")

    print("\n" + "=" * 80)
    print("🎯 GOAL: Find a prompt that eliminates false positives while keeping legitimate matches")

if __name__ == "__main__":
    main()
