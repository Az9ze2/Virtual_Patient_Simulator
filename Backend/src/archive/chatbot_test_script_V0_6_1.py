 #!/usr/bin/env python3
"""
Thai Medical OSCE Chatbot with Memory Management
Supports both GPT-4.1-mini (tunable) and GPT-5 (deterministic).
"""

import argparse
import json
import time
import sys
import os
import re
from typing import Dict, Any, Tuple, List
from dotenv import load_dotenv

from openai import OpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


class SimpleChatbotTester:
    """Chatbot tester with token tracking + memory-saving options"""

    def __init__(self, memory_mode: str = "summarize", model_choice: str = "gpt-4.1-mini", exam_mode: bool = False):
        """
        Initialize chatbot tester
        memory_mode options:
            - "none": keep all history
            - "truncate": drop oldest messages
            - "summarize": compress old turns into a summary

        model_choice options:
            - "gpt-4.1-mini" (supports tunable params)
            - "gpt-5" (deterministic, limited params)
        """
        load_dotenv()
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            print("❌ OPENAI_API_KEY not found in .env file")
            sys.exit(1)

        self.client = OpenAI(api_key=self.api_key)

        self.model_choice = model_choice

        # ✅ Handle model-specific generation params
        if self.model_choice == "gpt-4.1-mini":
            self.generation_params = {
                "model": "gpt-4.1-mini",
                "temperature": 0.7,
                "top_p": 0.85,
                "frequency_penalty": 0.6,
                "presence_penalty": 0.9,
                "max_completion_tokens": 600,
                "stop": ["🧑‍⚕️"]
            }
        elif self.model_choice == "gpt-5":
            self.generation_params = {
                "model": "gpt-5",
                "max_completion_tokens": 600
                # ⚠️ GPT-5 does not support temperature/top_p/penalties/stop
            }
        else:
            print(f"❌ Unsupported model: {self.model_choice}")
            sys.exit(1)

        # ✅ Apply exam mode seed
        if exam_mode:
            self.generation_params["seed"] = 1234  # fixed for reproducibility
            print("🎓 Exam mode enabled: fixed seed for standardized responses")
        else:
            print("🧪 Practice mode enabled: natural variation (no seed)")

        self.message_history: List[Any] = []
        self.total_tokens = 0
        self.input_tokens = 0
        self.output_tokens = 0

        self.memory_mode = memory_mode
        self.max_turns_before_memory = 10

        print(f"✓ Initialized model = {self.model_choice}, memory mode = {self.memory_mode}")

    def load_case_data(self, json_file_path: str) -> Dict[str, Any]:
        """Load case data from JSON"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                case_data = json.load(f)
            print(f"📋 Loaded case: {case_data['case_metadata']['case_title']}")
            return case_data
        except Exception as e:
            print(f"✗ Error loading case: {e}")
            sys.exit(1)

    def setup_conversation(self, case_data: Dict[str, Any]) -> str:
        """Prepare system prompt and initial context"""
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

        # ✅ Handle fallback_question format and add tracking
        fallback_data = simulation_instructions.get("fallback_question")
        
        # Handle cases where fallback_question is null or missing
        if fallback_data is None:
            self.questions_to_ask = []
            self.question_limit_type = None
            print("ℹ️ No fallback questions found in this case")
        else:
            # Extract question limit type
            self.question_limit_type = fallback_data.get("question_limit_type", "single")  # Default to single
            
            questions_data = fallback_data.get("questions", [])
            self.questions_to_ask = [
                {
                    "simulator_ask": q.get("text", ""),
                    "asked": False
                }
                for q in questions_data if q.get("text", "").strip()  # Only include non-empty questions
            ]
            
            if not self.questions_to_ask:
                print("ℹ️ No valid questions found in fallback_question")
            else:
                print(f"ℹ️ Question limit type: {self.question_limit_type}")

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
        {self._build_question_limit_rule()}
        รายการคำถาม (ถามเฉพาะ asked=False):
        {self._build_question_list()}
        
        **กฎสำคัญ**: ถ้ารายการคำถามแสดง "[ไม่มีคำถามเพิ่มเติม - ผู้เข้าสอบได้ครอบคลุมทุกหัวข้อแล้ว]" 
        ต้องตอบว่า "ไม่มีคำถามเพิ่มเติมค่ะ" หรือ "ไม่มีคำถามเพื่มเติมครับ" เท่านั้น ขึ้นอยู่กับเพศของผู้ป่วย ห้ามถามคำถามใหม่หรือเรื่องอื่น

        {dialogue_examples}
        """

        self.message_history = [SystemMessage(content=system_prompt)]
        return system_prompt
    
    def _update_question_status(self, student_input: str):
        """Update question status using GPT-4.1-mini with strict JSON output"""
        if not self.questions_to_ask:
            return
        
        # Only check unasked questions
        unasked_questions = [q for q in self.questions_to_ask if not q["asked"]]
        if not unasked_questions:
            return
        
        # Build numbered question list
        questions_list = "\n".join([f"{i+1}. {q['simulator_ask']}" for i, q in enumerate(unasked_questions)])

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
            analysis_response = self.client.chat.completions.create(
                messages=analysis_prompt,
                model="gpt-4.1-mini",
                temperature=0.1,
                max_completion_tokens=50
            )
            raw_output = analysis_response.choices[0].message.content.strip()
            
            # Parse strict JSON
            asked_indices = json.loads(raw_output)  # must be list of ints
            for idx in asked_indices:
                if 1 <= idx <= len(unasked_questions):
                    unasked_questions[idx-1]["asked"] = True
                    print(f"🔍 Marked as asked: {unasked_questions[idx-1]['simulator_ask'][:50]}...")
        
        except Exception as e:
            print(f"⚠️ Question analysis failed: {e}")

    
    def _keyword_fallback(self, student_input: str):
        """Fallback keyword matching system"""
        for q in self.questions_to_ask:
            if not q["asked"]:
                question_text = q["simulator_ask"]
                # Check if key terms from the question are mentioned in student input
                if any(keyword in student_input for keyword in question_text.split() if len(keyword) > 3):
                    q["asked"] = True
                    print(f"🔤 Keyword fallback: {q['simulator_ask'][:50]}...")
    
    def _build_question_limit_rule(self) -> str:
        """Build question limit rule based on question_limit_type"""
        if not self.questions_to_ask or self.question_limit_type is None:
            return ""  # No rules if no questions
        
        if self.question_limit_type == "multiple":
            return "สามารถถามได้หลายคำถาม"
        elif self.question_limit_type == "single":
            return "สามารถถามได้แค่คำถามเดียว"
        else:
            return "สามารถถามได้แค่คำถามเดียว"  # Default to single
    
    def _build_question_list(self) -> str:
        """Build formatted question list showing only unasked questions"""
        # Handle cases where no questions are available
        if not self.questions_to_ask:
            return "[ไม่มีคำถามเพิ่มเติมสำหรับกรณีนี้]"
        
        # Filter only unasked questions
        unasked_questions = [q for q in self.questions_to_ask if not q['asked']]
        
        if not unasked_questions:
            return "[ไม่มีคำถามเพิ่มเติม - ผู้เข้าสอบได้ครอบคลุมทุกหัวข้อแล้ว]\n\n**กฎสำคัญ**: ต้องตอบว่า 'ไม่มีคำถามเพิ่มเติมค่ะ' หรือ 'ไม่มีคำถามเพิ่มเติมครับ' เท่านั้น ขึ้นอยู่กับเพศของผู้ป่วย ห้ามถามคำถามใหม่"
        
        # Build the question list
        question_list = ""
        for q in unasked_questions:
            question_list += f"- {q['simulator_ask']}\n"
        
        return question_list.strip()
    
    def _refresh_system_prompt(self):
        """Update the system prompt with current question status"""
        # Find the original system message
        for i, msg in enumerate(self.message_history):
            if isinstance(msg, SystemMessage) and "# กฏเกณฑ์การตอบ" in msg.content:
                # This is our main system prompt, update it
                updated_content = self._build_updated_system_content(msg.content)
                self.message_history[i] = SystemMessage(content=updated_content)
                break
    
    def _build_updated_system_content(self, original_content: str) -> str:
        """Build updated system prompt with current question status"""
        # Find the question list section and replace it
        lines = original_content.split('\n')
        updated_lines = []
        skip_until_next_section = False
        
        for line in lines:
            if "รายการคำถาม (ถามเฉพาะ asked=False):" in line:
                # Start of question list section
                updated_lines.append(line)
                updated_lines.append("")
                # Insert current question list
                current_questions = self._build_question_list()
                updated_lines.append(current_questions)
                skip_until_next_section = True
            elif skip_until_next_section and (line.startswith("#") or line.strip().startswith("**กฎสำคัญ**") or line.strip() == "ถ้าถามคำถามเหล่านี้แล้ว"):
                # End of question list section
                skip_until_next_section = False
                updated_lines.append(line)
            elif not skip_until_next_section:
                updated_lines.append(line)
        
        return '\n'.join(updated_lines)

    def summarize_history(self):
        """Summarize old messages into a structured memory form and sync question flags"""
        if len(self.message_history) <= 6:
            return

        # Collect old conversation (everything except system + last 5 turns)
        old_msgs = self.message_history[1:-5]
        convo_text = "\n".join(
            [f"{'🧑‍⚕️' if isinstance(m, HumanMessage) else '👩‍⚕️'}: {m.content}" for m in old_msgs]
        )

        # Build explicit question status list from Python flags
        question_status_list = "\n".join(
            f"- simulator_ask: {q['simulator_ask']}\n  asked: {q.get('asked', False)}"
            for q in self.questions_to_ask
        )

        # Build stricter summarization prompt with injected asked/unasked state
        summarization_prompt = [
            {
                "role": "system",
                "content": (
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
            },
            {
                "role": "user",
                "content": (
                    f"นี่คือบทสนทนาที่ผ่านมา:\n{convo_text}\n\n"
                    f"นี่คือสถานะของคำถามเพิ่มเติม (จากระบบ):\n{question_status_list}"
                )
            }
        ]

        try:
            summary_resp = self.client.chat.completions.create(
                messages=summarization_prompt,
                model="gpt-4.1-mini",
                temperature=0.3,
                max_completion_tokens=350
            )
            summary_text = summary_resp.choices[0].message.content.strip()
        except Exception as e:
            summary_text = f"(สรุปข้อมูลไม่สำเร็จ: {e})"

        # Replace old history with system prompt + summary + recent turns
        self.message_history = [self.message_history[0]] + [
            SystemMessage(content=f"[สรุปการสนทนาก่อนหน้า]: {summary_text}")
        ] + self.message_history[-5:]

        # Debug printout
        print("\n🧾 Memory updated with new summary:\n")
        print(f"[SUMMARY] {summary_text}\n")
        print("📌 Current question flags:")
        for q in self.questions_to_ask:
            print(f"   - {q['simulator_ask']} | asked={q['asked']}")



    def manage_memory(self):
        """Decide whether to truncate or summarize"""
        if self.memory_mode == "truncate":
            self.message_history = [self.message_history[0]] + self.message_history[-10:]
        elif self.memory_mode == "summarize":
            self.summarize_history()

    def chat_turn(self, student_message: str) -> Tuple[str, float]:
        """Handle one conversation turn"""
        start_time = time.time()
        try:
            self.message_history.append(HumanMessage(content=student_message))
            
            # ✅ Update question tracking
            self._update_question_status(student_message)
            
            # ✅ Update system prompt with current question status
            self._refresh_system_prompt()

            if len(self.message_history) > self.max_turns_before_memory:
                self.manage_memory()

            messages_payload = []
            for m in self.message_history:
                if isinstance(m, SystemMessage):
                    messages_payload.append({"role": "system", "content": m.content})
                elif isinstance(m, HumanMessage):
                    messages_payload.append({"role": "user", "content": m.content})
                elif isinstance(m, AIMessage):
                    messages_payload.append({"role": "assistant", "content": m.content})

            response = self.client.chat.completions.create(
                messages=messages_payload,
                **self.generation_params
            )

            usage = response.usage
            self.input_tokens += usage.prompt_tokens
            self.output_tokens += usage.completion_tokens
            self.total_tokens += usage.total_tokens

            patient_response = response.choices[0].message.content
            self.message_history.append(AIMessage(content=patient_response))

            return patient_response, time.time() - start_time

        except Exception as e:
            return f"ขอโทษค่ะ เกิดข้อผิดพลาด: {str(e)}", 0.0

    def show_session_summary(self):
        """Show token usage and stats"""
        print("\n📊 สรุปการใช้งาน")
        print(f"📥 Input Tokens: {self.input_tokens}")
        print(f"📤 Output Tokens: {self.output_tokens}")
        print(f"📊 Total Tokens: {self.total_tokens}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["practice", "exam"], default="practice",
                        help="Choose practice (random variation) or exam (fixed seed) mode")
    parser.add_argument("--model", choices=["gpt-4.1-mini", "gpt-5"], default="gpt-4.1-mini",
                        help="Choose which model to use")
    parser.add_argument("--memory", choices=["none", "truncate", "summarize"], default="summarize",
                        help="Choose memory management strategy")
    args = parser.parse_args()

    case_file = r"C:\Users\ACER\Desktop\testAPI\extracted_data2\02_01_blood_in_stool.json"
    if not os.path.exists(case_file):
        print(f"❌ Missing case file: {case_file}")
        sys.exit(1)

    # Choose model here:
    # "gpt-4.1-mini" → tunable, interactive
    # "gpt-5"        → deterministic, strict
    bot = SimpleChatbotTester(memory_mode="summarize", model_choice="gpt-4.1-mini")

    case_data = bot.load_case_data(case_file)
    bot.setup_conversation(case_data)

    print(f"\n💬 เริ่มการสนทนา (quit = จบ) | Mode: {args.mode}, Model: {args.model}\n")
    while True:
        student = input("🧑‍⚕️ นักศึกษา: ").strip()
        if student.lower() in ["quit", "exit", "q"]:
            break
        reply, t = bot.chat_turn(student)
        print(f"👩‍⚕️ ผู้ป่วยจำลอง: {reply} (⏱ {t:.2f}s)")

    bot.show_session_summary()

if __name__ == "__main__":
    main()
