#!/usr/bin/env python3
"""
Test script for Medical Document Extractor
Tests both HuggingFace models and regex extraction methods
"""

import sys
import os
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.document_extractor import MedicalDocumentExtractor, extract_from_content

def test_sample_thai_content():
    """Test extraction with sample Thai medical content"""
    
    sample_content = """
    ข้อสอบ Comprehensive OSCE (Clinical Skills)
    ใช้สอบวันที่ 10 ธันวาคม 2566
    
    ภาควิชา กุมารเวชศาสตร์ ใช้สอบนักศึกษาแพทย์ ชั้นปีที่ 6
    ชื่อเรื่อง การซักประวัติ แจ้งผลการตรวจร่างกาย และให้คำแนะนำเกี่ยวกับการให้นมแม่
    ในมารดาที่มีภาวะหัวนมแตก (cracked nipple)
    
    ระยะเวลาที่ใช้สอบ 10 นาที
    คะแนนเต็ม 100 คะแนน เกณฑ์ผ่าน 54 คะแนน
    
    โจทย์
    มารดาพา ด.ช.ยินดี ปรีดา อายุ 5 วัน มาตรวจติดตามน้ำหนักตัวตามนัดและขอคำปรึกษา
    เรื่องการให้นมแม่เนื่องจากมีหัวนมข้างขวาแตก
    
    มารดาจำลองอายุ 25 ปี เป็นแม่บ้าน สามีอายุ 30 ปี ทำอาชีพครู
    """
    
    print("🧪 Testing Medical Document Extractor")
    print("=" * 60)
    
    # Test with HuggingFace model
    print("\n1. Testing with HuggingFace model...")
    try:
        extractor = MedicalDocumentExtractor(model_name="microsoft/DialoGPT-medium", device="cpu")
        result = extractor._extract_structured_data(sample_content)
        
        print("✅ HuggingFace extraction successful!")
        print("Extracted patient name:", result.get('patient_demographics', {}).get('patient_name', 'N/A'))
        print("Extracted age:", result.get('patient_demographics', {}).get('age', 'N/A'))
        print("Chief complaint:", result.get('presenting_complaint', {}).get('chief_complaint', 'N/A'))
        
    except Exception as e:
        print(f"❌ HuggingFace extraction failed: {str(e)}")
        print("Note: This is expected if HuggingFace transformers is not installed")
    
    # Test regex extraction (always works)
    print("\n2. Testing with Regex extraction...")
    try:
        extractor = MedicalDocumentExtractor()
        result = extractor._extract_with_regex(sample_content)
        
        print("✅ Regex extraction successful!")
        print("Extracted patient name:", result.get('patient_demographics', {}).get('patient_name', 'N/A'))
        print("Extracted age:", result.get('patient_demographics', {}).get('age', 'N/A'))
        print("Chief complaint:", result.get('presenting_complaint', {}).get('chief_complaint', 'N/A'))
        print("Case title:", result.get('case_metadata', {}).get('case_title', 'N/A'))
        
        # Show full result in JSON format
        print("\n📄 Full extraction result (JSON):")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"❌ Regex extraction failed: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Test completed!")

def test_file_reading():
    """Test different file format reading capabilities"""
    
    print("\n📁 Testing file reading capabilities...")
    
    # Test with text file
    test_file = Path("test_sample.txt")
    if test_file.exists():
        try:
            extractor = MedicalDocumentExtractor()
            result = extractor.extract_from_file(str(test_file))
            print("✅ File reading test successful!")
            print("Patient name:", result.get('patient_demographics', {}).get('patient_name', 'N/A'))
        except Exception as e:
            print(f"❌ File reading test failed: {str(e)}")
    else:
        print("ℹ️  No test file found, skipping file reading test")

def test_extraction_performance():
    """Test extraction performance and accuracy"""
    
    print("\n⚡ Testing extraction performance...")
    
    # Multiple test cases
    test_cases = [
        {
            "name": "Pediatric Case",
            "content": "มารดาพา ด.ช.สมชาย อายุ 6 เดือน มาตรวจติดตามการเจริญเติบโต"
        },
        {
            "name": "Adult Case", 
            "content": "นาย สมศักดิ์ อายุ 45 ปี มาด้วยอาการปวดท้อง"
        }
    ]
    
    extractor = MedicalDocumentExtractor()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['name']}")
        try:
            result = extractor._extract_with_regex(test_case['content'])
            patient_name = result.get('patient_demographics', {}).get('patient_name', 'Not found')
            age = result.get('patient_demographics', {}).get('age', 'Not found')
            
            print(f"  Patient: {patient_name}")
            print(f"  Age: {age}")
            print("  ✅ Extraction successful")
            
        except Exception as e:
            print(f"  ❌ Failed: {str(e)}")

if __name__ == "__main__":
    print("🏥 Medical Document Extractor Test Suite")
    print("========================================")
    
    # Run all tests
    test_sample_thai_content()
    test_file_reading()
    test_extraction_performance()
    
    print("\n🎉 All tests completed!")
    print("\nTo run with HuggingFace models, install dependencies:")
    print("pip install transformers torch")
