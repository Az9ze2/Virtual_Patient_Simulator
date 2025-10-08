#!/usr/bin/env python3
"""
Unified Thai Medical OSCE Chatbot with Memory Management
Handles both 01 (mother/guardian) and 02 (patient) case types automatically
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

# Add parent src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.prompt_config import PromptConfig


class UnifiedChatbotTester:
    """Unified chatbot tester that handles both 01 and 02 case types with token tracking + memory-saving options"""

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

        # Case type will be determined when loading case data
        self.case_type = None
        self.display_name = None

        print(f"✓ Initialized model = {self.model_choice}, memory mode = {self.memory_mode}")

    def load_case_data(self, json_file_path: str) -> Dict[str, Any]:
        """Load case data from JSON and determine case type"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                case_data = json.load(f)
            
            # Determine case type from filename
            filename = os.path.basename(json_file_path)
            self.case_type = PromptConfig.get_case_type_from_filename(filename)
            self.display_name = PromptConfig.get_display_name(self.case_type)
            
            if self.case_type == "unknown":
                print(f"⚠️ Warning: Could not determine case type from filename: {filename}")
                print("Defaulting to case type '01' (mother/guardian)")
                self.case_type = "01"
                self.display_name = PromptConfig.get_display_name("01")
            
            print(f"📋 Loaded case: {case_data['case_metadata']['case_title']}")
            print(f"🏷️ Detected case type: {self.case_type} ({'Mother/Guardian' if self.case_type == '01' else 'Patient'})")
            
            return case_data
        except Exception as e:
            print(f"✗ Error loading case: {e}")
            sys.exit(1)

    def setup_conversation(self, case_data: Dict[str, Any]) -> str:
        """Prepare system prompt and initial context using prompt configuration"""
        simulation_instructions = case_data['simulation_view']['simulation_instructions']
        
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

        # Extract sample dialogues using original logic
        dialogue_examples = PromptConfig.extract_sample_dialogues(case_data)
        
        # Build question limit rule and question list
        question_limit_rule = self._build_question_limit_rule()
        question_list = self._build_question_list()
        
        # Build system prompt based on case type
        if self.case_type == "01":
            system_prompt = PromptConfig.extract_data_and_build_prompt_01(
                case_data, question_limit_rule, question_list, dialogue_examples
            )
        elif self.case_type == "02":
            system_prompt = PromptConfig.extract_data_and_build_prompt_02(
                case_data, question_limit_rule, question_list, dialogue_examples
            )
        else:
            raise ValueError(f"Unsupported case type: {self.case_type}")

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
            if self.case_type == "01":
                return "[ไม่มีคำถามเพิ่มเติม - ผู้เข้าสอบได้ครอบคลุมทุกหัวข้อแล้ว]\n\n**กฎสำคัญ**: ต้องตอบว่า 'ไม่มีคำถามเพิ่มเติมค่ะ' เท่านั้น ห้ามถามคำถามใหม่"
            else:  # case_type == "02"
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

        # Get case-specific summary prompt
        if self.case_type == "01":
            summary_prompt_content = PromptConfig.get_summary_prompt_01()
        else:  # case_type == "02"
            summary_prompt_content = PromptConfig.get_summary_prompt_02()

        # Build stricter summarization prompt with injected asked/unasked state
        summarization_prompt = [
            {
                "role": "system",
                "content": summary_prompt_content
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
    parser = argparse.ArgumentParser(description="Unified Medical OSCE Chatbot - Handles both 01 and 02 case types")
    parser.add_argument("case_file", help="Path to the JSON case file (01_*.json or 02_*.json)")
    parser.add_argument("--mode", choices=["practice", "exam"], default="practice",
                        help="Choose practice (random variation) or exam (fixed seed) mode")
    parser.add_argument("--model", choices=["gpt-4.1-mini", "gpt-5"], default="gpt-4.1-mini",
                        help="Choose which model to use")
    parser.add_argument("--memory", choices=["none", "truncate", "summarize"], default="summarize",
                        help="Choose memory management strategy")
    args = parser.parse_args()

    if not os.path.exists(args.case_file):
        print(f"❌ Missing case file: {args.case_file}")
        sys.exit(1)

    # Initialize unified chatbot
    bot = UnifiedChatbotTester(
        memory_mode=args.memory, 
        model_choice=args.model,
        exam_mode=(args.mode == "exam")
    )

    case_data = bot.load_case_data(args.case_file)
    bot.setup_conversation(case_data)

    print(f"\n💬 เริ่มการสนทนา (quit = จบ) | Mode: {args.mode}, Model: {args.model}\n")
    while True:
        student = input("🧑‍⚕️ นักศึกษา: ").strip()
        if student.lower() in ["quit", "exit", "q"]:
            break
        reply, t = bot.chat_turn(student)
        print(f"{bot.display_name}: {reply} (⏱ {t:.2f}s)")

    bot.show_session_summary()

if __name__ == "__main__":
    main()
