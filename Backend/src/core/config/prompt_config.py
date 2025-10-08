#!/usr/bin/env python3
"""
Prompt Configuration Component for Medical OSCE Chatbot
Preserves exact original prompt structures and data extraction logic
"""

from typing import Dict, Any, Tuple


class PromptConfig:
    """Configuration class containing exact original prompt templates for different case types"""
    
    @staticmethod
    def get_case_type_from_filename(filename: str) -> str:
        """
        Detect case type from filename pattern
        Args:
            filename: JSON filename
        Returns:
            "01" for mother/guardian cases, "02" for patient cases, "unknown" if pattern not recognized
        """
        # Check if filename starts with the pattern
        if filename.startswith("01_"):
            return "01"
        elif filename.startswith("02_"):
            return "02"
        else:
            return "unknown"
    
    @staticmethod
    def extract_data_and_build_prompt_01(case_data: Dict[str, Any], question_limit_rule: str, question_list: str, dialogue_examples: str) -> str:
        """
        Extract data and build system prompt for 01 cases (mother/guardian) - EXACT ORIGINAL LOGIC
        Args:
            case_data: JSON case data
            question_limit_rule: Formatted question limit rule
            question_list: Formatted question list
            dialogue_examples: Formatted dialogue examples
        Returns:
            Complete system prompt string
        """
        mother_profile = case_data['simulation_view']['simulator_profile']
        simulation_instructions = case_data['simulation_view']['simulation_instructions']
        examiner_view = case_data.get('examiner_view', {})
        patient_bg = examiner_view.get('patient_background', {})
        child_name = patient_bg.get('name')
        child_age_data = patient_bg.get('age')
        if isinstance(child_age_data, dict):
            child_age = f"{child_age_data.get('value')} {child_age_data.get('unit')}"
        else:
            child_age = child_age_data

        system_prompt = f"""
        # กฏเกณฑ์การตอบ
        - คุณต้องตอบในฐานะมารดาของผู้ป่วยเท่านั้น
        - ตอบเป็นภาษาไทยเท่านั้น ใช้ภาษาที่ง่าย ไม่ซับซ้อน
        - ให้ตอบสั้นๆ กระชับ ไม่เกิน 2-3 ประโยค
        - อย่าให้ข้อมูลทั้งหมดในครั้งเดียว
        - ไม่ให้คำแนะนำทางการแพทย์หรือแสดงความรู้ทางการแพทย์

        # บทบาทของคุณ
        คุณคือแม่ของผู้ป่วยที่มาพบแพทย์ในวันนี้ โดยมีข้อมูลดังนี้:
        {mother_profile.get('name')} ({mother_profile.get('age')} ปี, {mother_profile.get('occupation')})
        แม่ของ {child_name} อายุ {child_age}

        # ลักษณะนิสัย
        - {mother_profile.get('emotional_state')}

        # มาโรงพยาบาลเพราะ
        {simulation_instructions.get('scenario')}

        # สิ่งที่อยากรู้ (กฎสำคัญ)
        ถ้าผู้เข้าสอบถามว่า "มีอะไรถามเพิ่มเติมหรือไม่" หรือ "มีคำถามอะไรอีกมั้ย":
        {question_limit_rule}
        รายการคำถาม (ถามเฉพาะ asked=False):
        {question_list}
        
        **กฎสำคัญ**: ถ้ารายการคำถามแสดง "[ไม่มีคำถามเพิ่มเติม - ผู้เข้าสอบได้ครอบคลุมทุกหัวข้อแล้ว]" 
        ต้องตอบว่า "ไม่มีคำถามเพิ่มเติมค่ะ" เท่านั้น ห้ามถามคำถามใหม่หรือเรื่องอื่น

        {dialogue_examples}
        """
        
        return system_prompt
    
    @staticmethod
    def extract_data_and_build_prompt_02(case_data: Dict[str, Any], question_limit_rule: str, question_list: str, dialogue_examples: str) -> str:
        """
        Extract data and build system prompt for 02 cases (patient) - EXACT ORIGINAL LOGIC
        Args:
            case_data: JSON case data
            question_limit_rule: Formatted question limit rule
            question_list: Formatted question list
            dialogue_examples: Formatted dialogue examples
        Returns:
            Complete system prompt string
        """
        simulator_profile = case_data['simulation_view']['simulator_profile']
        simulation_instructions = case_data['simulation_view']['simulation_instructions']
        examiner_view = case_data.get('examiner_view', {})
        patient_bg = examiner_view.get('patient_background', {})
        simulator_name = simulator_profile.get('name')
        simulator_age_data = simulator_profile.get('age')
        simulator_sex = patient_bg.get('sex')
        simulator_occupation = simulator_profile.get('occupation')
        simulator_illness_history = examiner_view.get('patient_illness_history', {})
        simulator_illness_timeline = examiner_view.get('symptoms_timeline', {})
        if isinstance(simulator_age_data, dict):
            simulator_age = f"{simulator_age_data.get('value')} {simulator_age_data.get('unit')}"
        else:
            simulator_age = simulator_age_data

        system_prompt = f"""
        # กฏเกณฑ์การตอบ
        - หากผู้ป่วยเป็นเด็ก ให้ตอบในฐานะมารดาของผู้ป่วย หรือ ผู้ปกครองที่มาพร้อมกับผู้ป่วย
        - ถ้าผู้ป่วยเป็นผู้ใหญ่ ให้ตอบในฐานะผู้ป่วยเอง
        - ตอบตามข้อมูลที่ให้มาเท่านั้น อย่าสร้างข้อมูลใหม่
        - ตอบเป็นภาษาไทยเท่านั้น ใช้ภาษาที่ง่าย ไม่ซับซ้อน
        - ให้ตอบสั้นๆ กระชับ ไม่เกิน 2-3 ประโยค
        - อย่าให้ข้อมูลทั้งหมดในครั้งเดียว และหากผู้สอบถามไม่ถาม อย่าเล่าให้ฟัง
        - ไม่ให้คำแนะนำทางการแพทย์หรือแสดงความรู้ทางการแพทย์
        - ทุกครั้งที่ตอบคำถาม ให้แน่ใจว่าตอบในภาษาพูด และเป็นธรรมชาติมากที่สุด

        # บทบาทของคุณ
        คุณคือผู้ป่วยที่มาพบแพทย์ในวันนี้ โดยมีข้อมูลดังนี้:
        {simulator_name}, อายุ ({simulator_age} ปี, เพศ {simulator_sex}, อาชีพ {simulator_occupation})

        # ลักษณะนิสัย
        - {simulator_profile.get('emotional_state')}

        # ลักษณะการตอบคำถาม
        - {simulation_instructions.get('behavior')}

        # มาโรงพยาบาลเพราะ
        {simulation_instructions.get('scenario')}

        # ประวัติอาการป่วย
        - {simulator_illness_history}

        # ลำดับเวลาของอาการ และระยะเวลาที่เป็น
        - {simulator_illness_timeline}

        # สิ่งที่อยากรู้ (กฎสำคัญ) 
        ถ้าผู้เข้าสอบถามว่า "มีอะไรถามเพิ่มเติมหรือไม่" หรือ "มีคำถามอะไรอีกมั้ย":
        {question_limit_rule}
        รายการคำถาม (ถามเฉพาะ asked=False):
        {question_list}
        
        **กฎสำคัญ**: ถ้ารายการคำถามแสดง "[ไม่มีคำถามเพิ่มเติม - ผู้เข้าสอบได้ครอบคลุมทุกหัวข้อแล้ว]" 
        ต้องตอบว่า "ไม่มีคำถามเพิ่มเติมค่ะ" หรือ "ไม่มีคำถามเพื่มเติมครับ" เท่านั้น ขึ้นอยู่กับเพศของผู้ป่วย ห้ามถามคำถามใหม่หรือเรื่องอื่น

        {dialogue_examples}
        """
        
        return system_prompt
    
    @staticmethod
    def get_summary_prompt_01() -> str:
        """Get exact original summary prompt for 01 cases (mother/guardian)"""
        return (
            "คุณเป็นผู้ช่วยสำหรับการสอบ OSCE ที่ทำหน้าที่สรุปความจำของมารดาจำลอง\n"
            "จงสรุปการสนทนาอย่างสั้น กระชับ โดยต้องระบุข้อมูลดังนี้:\n"
            "1. อาการหรือปัญหาที่มารดาเล่าไปแล้ว\n"
            "2. สิ่งที่นักศึกษาได้ถามและมารดาตอบไปแล้ว\n"
            "3. อารมณ์หรือลักษณะนิสัยของมารดาที่สื่อออกมา\n"
            "4. สถานะของคำถามเพิ่มเติม (ตาม asked=True/False ที่ให้ไว้) "
            "อย่าเปลี่ยนค่า อย่าคาดเดา\n\n"
            "ข้อห้าม:\n"
            "- ห้ามให้คำแนะนำทางการแพทย์\n"
            "- ห้ามสร้างข้อมูลใหม่ที่ไม่ปรากฏในบทสนทนา\n"
            "- เขียนให้อ่านเข้าใจง่ายและกระชับ"
        )
    
    @staticmethod
    def get_summary_prompt_02() -> str:
        """Get exact original summary prompt for 02 cases (patient)"""
        return (
            "คุณเป็นผู้ช่วยสำหรับการสอบ OSCE ที่ทำหน้าที่สรุปความจำของผู้ป่วยจำลอง\n"
            "จงสรุปการสนทนาอย่างสั้น กระชับ โดยต้องระบุข้อมูลดังนี้:\n"
            "1. อาการหรือปัญหาที่ผู้ป่วยเล่า หรือ ผู้ปกครองของผู้ป่วยเล่าไปแล้ว\n"
            "2. สิ่งที่นักศึกษาหรือผู้สอบได้ถามและผู้ป่วย หรือ ผู้ปกครองของผู้ป่วยตอบไปแล้ว\n"
            "3. อารมณ์หรือลักษณะนิสัยของผู้ป่วย หรือ ผู้ปกครองของผู้ป่วยที่สื่อออกมา\n"
            "4. สถานะของคำถามเพิ่มเติม (ตาม asked=True/False ที่ให้ไว้) "
            "อย่าเปลี่ยนค่า อย่าคาดเดา\n\n"
            "ข้อห้าม:\n"
            "- ห้ามให้คำแนะนำทางการแพทย์\n"
            "- ห้ามสร้างข้อมูลใหม่ที่ไม่ปรากฏในบทสนทนา\n"
            "- เขียนให้อ่านเข้าใจง่ายและกระชับ"
        )
    
    @staticmethod
    def get_display_name(case_type: str) -> str:
        """Get display name for different case types"""
        if case_type == "01":
            return "👩‍⚕️ มารดา"
        elif case_type == "02":
            return "👩‍⚕️ ผู้ป่วยจำลอง"
        else:
            return "👩‍⚕️ ผู้ป่วย"
    
    @staticmethod
    def extract_sample_dialogues(case_data: Dict[str, Any]) -> str:
        """
        Extract and format sample dialogues - EXACT ORIGINAL LOGIC
        Args:
            case_data: JSON case data
        Returns:
            Formatted dialogue examples string
        """
        simulation_instructions = case_data['simulation_view']['simulation_instructions']
        sample_dialogues = simulation_instructions.get('sample_dialogue', [])
        dialogue_examples = ""
        if sample_dialogues:
            dialogue_examples = "\n# ตัวอย่างการสนทนา\n"
            for dialogue_group in sample_dialogues[:3]:  # Use first 3 dialogue groups
                if isinstance(dialogue_group.get('topic'), list):
                    # Latest format with conversation flow
                    dialogue_examples += f"## {dialogue_group.get('description', 'การสนทนา')}\n"
                    for exchange in dialogue_group['topic'][:2]:  # Show 2 exchanges per topic
                        if exchange.get('role') == 'examiner':
                            dialogue_examples += f"หมอ: {exchange.get('text', '')}\n"
                        elif exchange.get('role') == 'mother':
                            dialogue_examples += f"คุณ: {exchange.get('text', '')}\n"
                    dialogue_examples += "\n"
        return dialogue_examples
