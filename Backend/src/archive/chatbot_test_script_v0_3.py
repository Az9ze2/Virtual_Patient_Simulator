#!/usr/bin/env python3
"""
Thai Medical OSCE Chatbot with Memory Management
Supports:
- Normal history mode
- Truncation (drop oldest messages)
- Summarization (compress old turns into a short summary)

Usage:
    python chatbot_test_script_v0.3.py
"""

import json
import time
import sys
import os
from typing import Dict, Any, Tuple, List
from dotenv import load_dotenv

# OpenAI direct client
from openai import OpenAI

# LangChain message format compatibility
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


class SimpleChatbotTester:
    """Chatbot tester with token tracking + memory-saving options"""

    def __init__(self, memory_mode: str = "summarize"):
        """
        Initialize chatbot tester
        memory_mode options:
            - "none": keep all history
            - "truncate": drop oldest messages
            - "summarize": compress old turns into a summary
        """
        load_dotenv()
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            print("❌ OPENAI_API_KEY not found in .env file")
            sys.exit(1)

        self.client = OpenAI(api_key=self.api_key)

        # Default parameters (can fine-tune later)
        self.generation_params = {
            "model": "gpt-5-mini",
            "max_completion_tokens": 600
        }


        self.message_history: List[Any] = []
        self.total_tokens = 0
        self.input_tokens = 0
        self.output_tokens = 0

        # Memory control
        self.memory_mode = memory_mode  # "none", "truncate", "summarize"
        self.max_turns_before_memory = 10  # trigger memory handling

        print(f"✓ Initialized GPT-5 with memory mode = {self.memory_mode}")

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
        mother_profile = case_data['simulation_view']['mother_profile']
        simulation_instructions = case_data['simulation_view']['simulation_instructions']
        examiner_view = case_data.get('examiner_view', {})
        patient_bg = examiner_view.get('patient_background', {})
        child_name = patient_bg.get('child_name', 'ด.ช.ยินดี ปรีดา')
        child_age_data = patient_bg.get('child_age', patient_bg.get('child_age_days_or_months', '5 วัน'))
        if isinstance(child_age_data, dict):
            child_age = f"{child_age_data.get('value', 5)} {child_age_data.get('unit', 'วัน')}"
        else:
            child_age = child_age_data
        questions_to_ask = simulation_instructions.get('questions_to_ask_examiner', [])
        question_list = ""
        for q in questions_to_ask:
            question_text = q.get('examiner_questions', q.get('questions', ''))
            question_list += f"→ {question_text}\n"

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
        - ตอบเป็นภาษาไทยเท่านั้น ใช้ภาษาที่ง่าย ไม่ซับซ้อน
        - ให้ตอบสั้นๆ กระชับ ไม่เกิน 2-3 ประโยค
        - ไม่จำเป็นต้องพูดถึงการแสดงท่าทางกายภาพ
        - อย่าให้ข้อมูลทั้งหมดในครั้งเดียว 
        - ไม่ให้คำแนะนำทางการแพทย์เด็ดขาด

        # บทบาทของคุณ
        {mother_profile.get('name')} ({mother_profile.get('age')} ปี, {mother_profile.get('occupation')})
        แม่ของ {child_name} อายุ {child_age}

        # มาโรงพยาบาลเพราะ
        {simulation_instructions.get('scenario')}

        # ลักษณะนิสัย
        - {mother_profile.get('emotional_state')}

        {dialogue_examples}

        # สิ่งที่อยากรู้
        - สามารถถามคำถามต่อไปนี้ได้ต่อเมื่อคุณหมอเปิดโอกาสให้ถาม
        - โดยให้ถามคำถามได้ทีละ 1 ข้อเท่านั้น
        ลิสต์คำถามที่อยากรู้:
        {question_list}
        """

        self.message_history = [SystemMessage(content=system_prompt)]
        return system_prompt

    def summarize_history(self):
        """Summarize old messages in to a shorter form"""
        if len(self.message_history) <= 6:
            return

        old_msgs = self.message_history[1:-5]  # keep system + last 5 messages
        convo_text = "\n".join(
            [f"{'🧑‍⚕️' if isinstance(m, HumanMessage) else '👩‍⚕️'}: {m.content}" for m in old_msgs]
        )

        summarization_prompt = [
            {"role": "system", "content": "สรุปการสนทนาให้สั้น กระชับ เพื่อเก็บเป็นความทรงจำของคนไข้"},
            {"role": "user", "content": convo_text}
        ]

        summary_resp = self.client.chat.completions.create(
            messages=summarization_prompt,
            model="gpt-5-mini",  # cheaper model for summarization
            max_completion_tokens=200  # ✅ updated
        )

        summary_text = summary_resp.choices[0].message.content.strip()
        # Replace old messages with one summary system note
        self.message_history = [self.message_history[0]] + [
            SystemMessage(content=f"[สรุปการสนทนาก่อนหน้า]: {summary_text}")
        ] + self.message_history[-5:]

    def manage_memory(self):
        """Decide whether to truncate or summarize"""
        if self.memory_mode == "truncate":
            # keep system + last N messages
            self.message_history = [self.message_history[0]] + self.message_history[-10:]
        elif self.memory_mode == "summarize":
            self.summarize_history()

    def chat_turn(self, student_message: str) -> Tuple[str, float]:
        """Handle one conversation turn"""
        start_time = time.time()
        try:
            self.message_history.append(HumanMessage(content=student_message))

            # memory check
            if len(self.message_history) > self.max_turns_before_memory:
                self.manage_memory()

            # convert to OpenAI format
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
    case_file = "output.json"
    if not os.path.exists(case_file):
        print(f"❌ Missing case file: {case_file}")
        sys.exit(1)

    # memory_mode = "none" | "truncate" | "summarize"
    bot = SimpleChatbotTester(memory_mode="summarize")
    case_data = bot.load_case_data(case_file)
    bot.setup_conversation(case_data)

    print("\n💬 เริ่มการสนทนา (quit = จบ)\n")
    while True:
        student = input("🧑‍⚕️ นักศึกษา: ").strip()
        if student.lower() in ["quit", "exit", "q"]:
            break
        reply, t = bot.chat_turn(student)
        print(f"👩‍⚕️ มารดา: {reply} (⏱ {t:.2f}s)")

    bot.show_session_summary()


if __name__ == "__main__":
    main()