import json
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from openai import OpenAI
import anthropic
from pydantic import BaseModel

class PatientCase(BaseModel):
    case_metadata: Dict[str, Any]
    patient_demographics: Dict[str, Any]
    family_context: Dict[str, Any]
    presenting_complaint: Dict[str, Any]
    medical_history: Dict[str, Any]
    current_status: Dict[str, Any]
    patient_personality: Dict[str, Any]
    conversation_guidelines: Dict[str, Any]
    learning_objectives: Dict[str, Any]
    scenario_progression: Dict[str, Any]

class OSCEDataExtractor:
    """
    AI-powered extraction model to convert OSCE exam documents 
    into structured JSON for virtual patient system
    """
    
    def __init__(self, model_type="openai", api_key=None):
        self.model_type = model_type
        if model_type == "openai":
            self.client = OpenAI(api_key=api_key)
        elif model_type == "anthropic":
            self.client = anthropic.Anthropic(api_key=api_key)
        
        self.extraction_template = self._get_extraction_template()
    
    def _get_extraction_template(self) -> str:
        return """
        คุณเป็น AI ที่เชี่ยวชาญในการแปลงเอกสารสอบ OSCE เป็น JSON สำหรับระบบผู้ป่วยเสมือน
        
        งานของคุณ: แปลงเอกสารสอบ OSCE เป็น JSON ที่มีโครงสร้างตามที่กำหนด
        
        สิ่งสำคัญ:
        1. ระบุว่าใครเป็นคนพูด (ผู้ป่วย, มารดา, บิดา)
        2. แยกแยะอาการและข้อมูลที่ควรเปิดเผยทันที vs ต้องถามเจาะจง
        3. สร้างบุคลิกผู้ป่วยที่สมจริง (กังวล, พูดมาก, พูดน้อย)
        4. ใช้ภาษาไทยธรรมดา ไม่ใช่ศัพท์การแพทย์
        
        JSON Template:
        {
          "case_metadata": {
            "case_id": "string",
            "case_title": "string", 
            "medical_specialty": "string",
            "difficulty_level": "basic/intermediate/advanced",
            "exam_duration": "number",
            "total_score": "number",
            "pass_threshold": "number"
          },
          "patient_demographics": {
            "patient_name": "string",
            "age": "string/number",
            "gender": "string", 
            "occupation": "string",
            "relationship": "ตัวผู้ป่วย/มารดา/บิดา"
          },
          "family_context": {
            "family_structure": {},
            "primary_caregiver": "string",
            "support_system": [],
            "living_situation": "string"
          },
          "presenting_complaint": {
            "chief_complaint": "string",
            "duration": "string",
            "severity": "string", 
            "associated_symptoms": []
          },
          "medical_history": {
            "pregnancy_history": {},
            "birth_history": {},
            "past_medical_history": [],
            "medication_history": [],
            "family_history": [],
            "developmental_history": {}
          },
          "current_status": {
            "general_condition": "string",
            "vital_signs": {},
            "physical_examination": {},
            "laboratory_results": {}
          },
          "patient_personality": {
            "communication_style": "string",
            "anxiety_level": "low/medium/high",
            "cooperation_level": "string",
            "knowledge_level": "string"
          },
          "conversation_guidelines": {
            "initial_responses": [],
            "information_revelation_pattern": {},
            "typical_questions_from_patient": [],
            "responses_to_specific_questions": {}
          },
          "learning_objectives": {
            "primary_skills": [],
            "assessment_criteria": [],
            "expected_student_actions": []
          },
          "scenario_progression": {
            "opening_scenario": "string",
            "key_information_to_elicit": [],
            "red_flags": [],
            "case_closure": "string"
          }
        }
        """
    
    def extract_from_text(self, osce_text: str) -> PatientCase:
        """
        Extract structured data from OSCE document text
        """
        prompt = f"""
        {self.extraction_template}
        
        เอกสาร OSCE ที่ต้องแปลง:
        {osce_text}
        
        กรุณาแปลงเป็น JSON ตามโครงสร้างที่กำหนด:
        """
        
        if self.model_type == "openai":
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.extraction_template},
                    {"role": "user", "content": f"เอกสาร OSCE:\n{osce_text}"}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            result = response.choices[0].message.content
            
        elif self.model_type == "anthropic":
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            result = response.content[0].text
        
        # Parse JSON from response
        try:
            # Extract JSON from response (remove markdown formatting if any)
            json_match = re.search(r'```json\n?(.*?)\n?```', result, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Assume the entire response is JSON
                json_str = result
            
            json_data = json.loads(json_str)
            return PatientCase(**json_data)
            
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            print(f"Raw response: {result}")
            raise
    
    def extract_from_file(self, file_path: str) -> PatientCase:
        """
        Extract data from OSCE file (supports .txt, .docx)
        """
        if file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        elif file_path.endswith('.docx'):
            from docx import Document
            doc = Document(file_path)
            content = '\n'.join([p.text for p in doc.paragraphs])
        else:
            raise ValueError("Unsupported file format. Use .txt or .docx")
        
        return self.extract_from_text(content)
    
    def batch_extract(self, file_paths: List[str]) -> Dict[str, PatientCase]:
        """
        Extract multiple OSCE cases at once
        """
        results = {}
        for file_path in file_paths:
            try:
                case = self.extract_from_file(file_path)
                results[file_path] = case
                print(f"✅ Successfully extracted: {file_path}")
            except Exception as e:
                print(f"❌ Failed to extract {file_path}: {e}")
                results[file_path] = None
        
        return results
    
    def save_case_to_json(self, case: PatientCase, output_path: str):
        """
        Save extracted case to JSON file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(case.dict(), f, ensure_ascii=False, indent=2)
    
    def validate_extraction(self, case: PatientCase) -> Dict[str, bool]:
        """
        Validate the quality of extraction
        """
        validation_results = {
            "has_demographics": bool(case.patient_demographics.get("age")),
            "has_chief_complaint": bool(case.presenting_complaint.get("chief_complaint")),
            "has_personality": bool(case.patient_personality.get("communication_style")),
            "has_conversation_guidelines": bool(case.conversation_guidelines.get("initial_responses")),
            "has_learning_objectives": bool(case.learning_objectives.get("primary_skills"))
        }
        
        return validation_results

# Example usage and testing
def test_extraction():
    """
    Test the extraction model with sample OSCE content
    """
    
    # Sample OSCE content (from your documents)
    sample_osce = """
    ด.ช.เอก สุขสันต์ อายุ 2 เดือน มารดาพามารับวัคซีนตามนัด EPI เด็กสบายดี
    
    มารดาจำลองอายุ 25 ปี เป็นแม่บ้าน สามีอายุ 31 ปี ทำอาชีพตำรวจ
    บุตรชายชื่อ ด.ช.เอก สุขสันต์ อายุ 2 เดือน เป็นลูกคนแรก
    
    ด.ช.เอก สุขสันต์ อายุ 2 เดือน มารดาพามารับวัคซีนตามนัด EPI 
    มารดากังวลเรื่องหนังหุ้มอวัยวะเพศชายของบุตรไม่เปิด
    
    เป็นลูกคนแรก แข็งแรงดี ปัจจุบันกินนมแม่อย่างเดียวทุก 2-3 ชั่วโมง 
    โดยกินครั้งละ 30 นาที ไม่ได้กินอาหารเสริม
    
    ถ่ายอุจจาระเป็นสีเหลืองวันละ 2-3 ครั้ง ปัสสาวะวันละ 6-7 ครั้ง 
    ปัสสาวะพุ่งดี ไม่มีการโป่งพองที่ปลายอวัยวะเพศชายหลังปัสสาวะเสร็จ
    """
    
    # Initialize extractor
    extractor = OSCEDataExtractor(model_type="openai", api_key="your-api-key")
    
    # Extract case
    try:
        case = extractor.extract_from_text(sample_osce)
        print("✅ Extraction successful!")
        
        # Validate
        validation = extractor.validate_extraction(case)
        print(f"Validation results: {validation}")
        
        # Save to file
        extractor.save_case_to_json(case, "extracted_case.json")
        print("💾 Saved to extracted_case.json")
        
        return case
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return None

if __name__ == "__main__":
    # Run test
    test_case = test_extraction()
    
    if test_case:
        print("\n📋 Extracted Case Summary:")
        print(f"Patient: {test_case.patient_demographics.get('patient_name')}")
        print(f"Age: {test_case.patient_demographics.get('age')}")
        print(f"Chief Complaint: {test_case.presenting_complaint.get('chief_complaint')}")
        print(f"Personality: {test_case.patient_personality.get('communication_style')}")