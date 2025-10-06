#!/usr/bin/env python3
"""
Analyze why fallback questions were triggered in cases 8, 9, and 10
when our basic history questions shouldn't match them.
"""

import json
import os
from pathlib import Path

def analyze_fallback_questions():
    """Analyze the fallback questions in cases that had them addressed"""
    
    data_dir = Path("C:/Users/acer/Desktop/IRPC_Internship/Virtual_Patient_Simulator/Backend/Extracted_Data_json")
    
    # Cases that showed fallback questions addressed
    cases_to_check = [
        ("01_08_gastroenteritis.json", "1/1 addressed"),
        ("01_09_hydrocele.json", "2/2 addressed"), 
        ("01_10_iron_def-ข้อสอบ_ฝึก_SP.json", "4/4 addressed")
    ]
    
    # Our basic history questions used in the test
    basic_questions = [
        "สวัสดีครับ วันนี้มีเรื่องอะไรให้ช่วยครับ",
        "น้องชื่ออะไรครับ อายุเท่าไหร่",
        "อาการเป็นมาตั้งแต่เมื่อไหร่ครับ",
        "มีอาการอื่นร่วมด้วยไหมครับ",
        "เคยไปหาหมอมาก่อนไหมครับ"
    ]
    
    print("🔍 Analyzing Fallback Question Triggering")
    print("=" * 60)
    print(f"📝 Our test questions:")
    for i, q in enumerate(basic_questions, 1):
        print(f"   {i}. {q}")
    print()
    
    for case_file, status in cases_to_check:
        case_path = data_dir / case_file
        
        print(f"📄 {case_file} ({status})")
        print("-" * 50)
        
        if not case_path.exists():
            print("❌ File not found")
            continue
            
        try:
            with open(case_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Get fallback questions
            fallback_data = data.get('simulation_view', {}).get('simulation_instructions', {}).get('fallback_question')
            
            if fallback_data is None:
                print("ℹ️ No fallback questions found")
                continue
                
            if isinstance(fallback_data, str):
                print(f"⚠️ Fallback question is string: {fallback_data}")
                continue
                
            if not isinstance(fallback_data, dict):
                print(f"⚠️ Unexpected fallback_question type: {type(fallback_data)}")
                continue
            
            print(f"🎯 Question limit type: {fallback_data.get('question_limit_type', 'unknown')}")
            
            questions = fallback_data.get('questions', [])
            print(f"📋 Total fallback questions: {len(questions)}")
            
            for i, q in enumerate(questions, 1):
                if isinstance(q, dict):
                    question_text = q.get('text', '')
                    print(f"   {i}. {question_text}")
                else:
                    print(f"   {i}. {q}")
            
            print(f"\n🤔 Analysis: Why might these be triggered by our basic questions?")
            
            # Look for potential matches
            for basic_q in basic_questions:
                for i, fallback_q in enumerate(questions, 1):
                    if isinstance(fallback_q, dict):
                        fallback_text = fallback_q.get('text', '')
                    else:
                        fallback_text = str(fallback_q)
                    
                    # Check for potential keyword overlap
                    basic_words = set(basic_q.split())
                    fallback_words = set(fallback_text.split())
                    
                    # Remove common Thai words that might cause false matches
                    common_thai = {'ครับ', 'คะ', 'ค่ะ', 'ไหม', 'หรือ', 'เป็น', 'มี', 'ใน', 'ที่', 'ของ', 'และ', 'กับ', 'จาก', 'ไป', 'มา', 'ได้', 'แล้ว', 'นี้', 'นั่น', 'โรค', 'เรื่อง', 'อะไร', 'อย่างไร', 'เท่าไหร่'}
                    
                    basic_meaningful = basic_words - common_thai
                    fallback_meaningful = fallback_words - common_thai
                    
                    overlap = basic_meaningful & fallback_meaningful
                    if overlap:
                        print(f"   🔗 Potential match between:")
                        print(f"      Basic Q: '{basic_q}'")
                        print(f"      Fallback Q{i}: '{fallback_text}'")
                        print(f"      Overlap: {overlap}")
            
            print()
            
        except Exception as e:
            print(f"❌ Error analyzing {case_file}: {e}")
            continue

if __name__ == "__main__":
    analyze_fallback_questions()
