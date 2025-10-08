#!/usr/bin/env python3
"""
Test script for prompt configuration functionality
"""

import sys
import os
from pathlib import Path

# Add core directory to path
sys.path.append(str(Path(__file__).parent.parent.parent / "core"))

from config.prompt_config import PromptConfig

def test_case_type_detection():
    """Test case type detection from filenames"""
    print("🧪 Testing case type detection...")
    
    test_cases = [
        ("01_01_breast_feeding_problems.json", "01"),
        ("01_02_CHC_9_months.json", "01"),
        ("02_01_blood_in_stool.json", "02"),
        ("02_02_breaking_bad_news.json", "02"),
        ("random_filename.json", "unknown"),
        ("03_01_some_case.json", "unknown")
    ]
    
    for filename, expected in test_cases:
        result = PromptConfig.get_case_type_from_filename(filename)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"  {status}: '{filename}' -> '{result}' (expected: '{expected}')")
    
    print()

def test_display_names():
    """Test display name generation"""
    print("🧪 Testing display names...")
    
    test_cases = [
        ("01", "👩‍⚕️ มารดา"),
        ("02", "👩‍⚕️ ผู้ป่วยจำลอง"),
        ("unknown", "👩‍⚕️ ผู้ป่วย")
    ]
    
    for case_type, expected in test_cases:
        result = PromptConfig.get_display_name(case_type)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"  {status}: '{case_type}' -> '{result}' (expected: '{expected}')")
    
    print()

def test_prompt_generation():
    """Test prompt generation with sample data"""
    print("🧪 Testing prompt generation...")
    
    # Mock case data for testing
    sample_case_data_01 = {
        "simulation_view": {
            "simulator_profile": {
                "name": "นางสาวแสง",
                "age": "25",
                "occupation": "แม่บ้าน",
                "emotional_state": "กังวลเป็นกรด"
            },
            "simulation_instructions": {
                "scenario": "ลูกไม่ยอมดูดนม",
                "sample_dialogue": []
            }
        },
        "examiner_view": {
            "patient_background": {
                "name": "เด็กหญิงน้ำใส",
                "age": {"value": 2, "unit": "เดือน"}
            }
        }
    }
    
    sample_case_data_02 = {
        "simulation_view": {
            "simulator_profile": {
                "name": "นายสมชาย",
                "age": {"value": 45, "unit": "ปี"},
                "occupation": "เกษตรกร",
                "emotional_state": "กังวลเล็กน้อย"
            },
            "simulation_instructions": {
                "scenario": "มีเลือดในอุจจาระ",
                "behavior": "พูดช้าและไต่ถาม",
                "sample_dialogue": []
            }
        },
        "examiner_view": {
            "patient_background": {
                "sex": "ชาย"
            },
            "patient_illness_history": "เริ่มมีอาการมา 1 สัปดาห์",
            "symptoms_timeline": "เช้ามดเข้าส้วม เห็นเลือดสดๆ"
        }
    }
    
    # Test 01 prompt generation
    try:
        prompt_01 = PromptConfig.extract_data_and_build_prompt_01(
            sample_case_data_01, "สามารถถามได้แค่คำถามเดียว", "- คำถามทดสอบ", ""
        )
        print("  ✅ PASS: Case type 01 prompt generation successful")
        
        # Check if key elements are present
        if "มารดาของผู้ป่วยเท่านั้น" in prompt_01 and "นางสาวแสง" in prompt_01:
            print("  ✅ PASS: Case type 01 prompt contains expected elements")
        else:
            print("  ❌ FAIL: Case type 01 prompt missing expected elements")
            
    except Exception as e:
        print(f"  ❌ FAIL: Case type 01 prompt generation failed: {e}")
    
    # Test 02 prompt generation
    try:
        prompt_02 = PromptConfig.extract_data_and_build_prompt_02(
            sample_case_data_02, "สามารถถามได้แค่คำถามเดียว", "- คำถามทดสอบ", ""
        )
        print("  ✅ PASS: Case type 02 prompt generation successful")
        
        # Check if key elements are present
        if "ผู้ป่วยที่มาพบแพทย์" in prompt_02 and "นายสมชาย" in prompt_02:
            print("  ✅ PASS: Case type 02 prompt contains expected elements")
        else:
            print("  ❌ FAIL: Case type 02 prompt missing expected elements")
            
    except Exception as e:
        print(f"  ❌ FAIL: Case type 02 prompt generation failed: {e}")
    
    print()

def test_summary_prompts():
    """Test summary prompt generation"""
    print("🧪 Testing summary prompts...")
    
    try:
        summary_01 = PromptConfig.get_summary_prompt_01()
        if "มารดาจำลอง" in summary_01:
            print("  ✅ PASS: Case type 01 summary prompt contains expected content")
        else:
            print("  ❌ FAIL: Case type 01 summary prompt missing expected content")
            
        summary_02 = PromptConfig.get_summary_prompt_02()
        if "ผู้ป่วยจำลอง" in summary_02:
            print("  ✅ PASS: Case type 02 summary prompt contains expected content")
        else:
            print("  ❌ FAIL: Case type 02 summary prompt missing expected content")
            
    except Exception as e:
        print(f"  ❌ FAIL: Summary prompt generation failed: {e}")
    
    print()

def main():
    print("🚀 Starting Prompt Configuration Tests\n")
    
    test_case_type_detection()
    test_display_names()
    test_prompt_generation()
    test_summary_prompts()
    
    print("✨ Test completed!")

if __name__ == "__main__":
    main()
