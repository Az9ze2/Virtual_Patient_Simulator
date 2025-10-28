"""
Word Correction Service for Medical Conversation
Corrects medical terminology and common speech-to-text errors in Thai language
Uses JSON dictionary files for medical and everyday terms
"""

import os
import json
import logging
from openai import OpenAI
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class WordCorrectionService:
    """Service for correcting transcribed text before sending to chatbot"""
    
    def __init__(self):
        """Initialize the word correction service"""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"  # Fast and cost-effective model for corrections
        
        # Load dictionaries from JSON files
        self.medical_dictionary = self._load_json_dictionary('medical_dictionary.json')
        self.everyday_dictionary = self._load_json_dictionary('everyday_dictionary.json')
        
        # Build context from loaded dictionaries
        self.medical_terms_context = self._build_medical_context()
        self.common_mistakes = self._build_mistakes_context()
        self.correction_rules = self._build_rules_context()
        
        logger.info("✅ Word Correction Service initialized")
        logger.info(f"📚 Loaded {len(self.medical_dictionary.get('terms', {}))} medical terms")
        logger.info(f"📝 Loaded {len(self.everyday_dictionary.get('common_words', {}))} everyday words")
        
    def _load_json_dictionary(self, filename: str) -> Dict:
        """Load dictionary from JSON file"""
        try:
            # Try multiple possible paths
            possible_paths = [
                os.path.join(os.path.dirname(__file__), filename),
                os.path.join(os.path.dirname(__file__), '..', 'data', 'Dictionary_correction', filename),
                os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'Dictionary_correction', filename),
                filename  # Current directory
            ]
            
            for dict_path in possible_paths:
                if os.path.exists(dict_path):
                    with open(dict_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        logger.info(f"✅ Loaded dictionary: {dict_path}")
                        return data
            
            # If file not found, return empty structure
            logger.warning(f"⚠️ Dictionary file not found: {filename}, using empty dictionary")
            return self._get_empty_dictionary_structure()
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error in {filename}: {e}")
            return self._get_empty_dictionary_structure()
        except Exception as e:
            logger.error(f"❌ Error loading dictionary {filename}: {e}")
            return self._get_empty_dictionary_structure()
    
    def _get_empty_dictionary_structure(self) -> Dict:
        """Return empty dictionary structure"""
        return {
            "terms": {},
            "common_mistakes": {},
            "categories": {},
            "examples": []
        }
    
    def _build_medical_context(self) -> str:
        """Build medical context from loaded dictionary"""
        context = "คำศัพท์ทางการแพทย์ที่พบบ่อย (Common Medical Terms):\n\n"
        
        # Add terms by category
        categories = self.medical_dictionary.get('categories', {})
        for category_name, category_data in categories.items():
            context += f"=== {category_data.get('name_th', category_name)} ===\n"
            
            terms = category_data.get('terms', [])
            for term in terms:
                if isinstance(term, dict):
                    main_term = term.get('main', '')
                    alternatives = term.get('alternatives', [])
                    if alternatives:
                        context += f"- {main_term} ({', '.join(alternatives)})\n"
                    else:
                        context += f"- {main_term}\n"
                else:
                    context += f"- {term}\n"
            context += "\n"
        
        # Add individual terms not in categories
        terms = self.medical_dictionary.get('terms', {})
        if terms:
            context += "=== คำศัพท์เพิ่มเติม (Additional Terms) ===\n"
            for term, info in terms.items():
                if isinstance(info, dict):
                    alternatives = info.get('alternatives', [])
                    if alternatives:
                        context += f"- {term} ({', '.join(alternatives)})\n"
                    else:
                        context += f"- {term}\n"
                elif isinstance(info, str):
                    context += f"- {term} ({info})\n"
                else:
                    context += f"- {term}\n"
        
        return context
    
    def _build_mistakes_context(self) -> str:
        """Build common mistakes context from dictionaries"""
        context = "ข้อผิดพลาดที่พบบ่อยจาก Speech-to-Text:\n\n"
        
        # Medical mistakes
        medical_mistakes = self.medical_dictionary.get('common_mistakes', {})
        if medical_mistakes:
            context += "=== คำศัพท์การแพทย์ที่มักเข้าใจผิด ===\n"
            for wrong, correct in medical_mistakes.items():
                context += f'- "{wrong}" ❌ → "{correct}" ✅\n'
            context += "\n"
        
        # Everyday mistakes
        everyday_mistakes = self.everyday_dictionary.get('common_mistakes', {})
        if everyday_mistakes:
            context += "=== คำทั่วไปที่มักเข้าใจผิด ===\n"
            for wrong, correct in everyday_mistakes.items():
                context += f'- "{wrong}" ❌ → "{correct}" ✅\n'
            context += "\n"
        
        return context
    
    def _build_rules_context(self) -> str:
        """Build correction rules from dictionaries"""
        rules = []
        
        # Get rules from medical dictionary
        medical_rules = self.medical_dictionary.get('correction_rules', [])
        rules.extend(medical_rules)
        
        # Get rules from everyday dictionary
        everyday_rules = self.everyday_dictionary.get('correction_rules', [])
        rules.extend(everyday_rules)
        
        if not rules:
            # Default rules if none provided
            rules = [
                "ถ้าพูดถึง 'ตำแหน่งที่ปวด' → มักจะเป็นชื่ออวัยวะหรือส่วนของร่างกาย",
                "ถ้าพูดถึง 'อาการ' → มักจะเป็น ไข้, ปวด, เจ็บ, คลื่นไส้, อาเจียน",
                "ถ้าพูดถึง 'การรักษา' → มักจะเป็น ยา, ฉีด, ตรวจ, ผ่าตัด",
                "ถ้าพูดถึง 'ระยะเวลา' → มักจะเป็น วัน, สัปดาห์, เดือน, ปี",
                "ถ้าพูดถึง 'ความถี่' → มักจะเป็น บ่อย, นานๆ ครั้ง, ทุกวัน"
            ]
        
        context = "กฎการแก้ไขตามบริบท:\n\n"
        for i, rule in enumerate(rules, 1):
            context += f"{i}. {rule}\n"
        
        return context
    
    def correct_text(self, transcribed_text: str, context: str = "") -> Dict[str, Any]:
        """
        Correct transcribed text for medical terminology and common errors
        
        Args:
            transcribed_text: Raw text from Whisper STT
            context: Optional context about the conversation
            
        Returns:
            Dictionary with corrected text and metadata
        """
        if not transcribed_text or not transcribed_text.strip():
            return {
                "original_text": transcribed_text,
                "corrected_text": transcribed_text,
                "corrections_made": False,
                "changes": []
            }
        
        try:
            logger.info(f"🔧 Correcting text: {transcribed_text[:100]}...")
            
            # Build correction prompt
            correction_prompt = self._build_correction_prompt(transcribed_text, context)
            
            # Call GPT for corrections
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": correction_prompt
                    }
                ],
                temperature=0.01,  # Very low for consistency
                max_tokens=500,
                top_p=0.9
            )
            
            corrected_text = response.choices[0].message.content.strip()
            
            # Detect if corrections were made
            corrections_made = corrected_text != transcribed_text
            changes = self._identify_changes(transcribed_text, corrected_text) if corrections_made else []
            
            logger.info(f"✅ Text correction complete. Changes made: {corrections_made}")
            if changes:
                logger.info(f"📝 Changes: {changes}")
            
            return {
                "original_text": transcribed_text,
                "corrected_text": corrected_text,
                "corrections_made": corrections_made,
                "changes": changes,
                "model_used": self.model
            }
            
        except Exception as e:
            logger.error(f"❌ Error correcting text: {str(e)}")
            # Return original text if correction fails
            return {
                "original_text": transcribed_text,
                "corrected_text": transcribed_text,
                "corrections_made": False,
                "error": str(e)
            }
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt with dictionary-based context"""
        # Get examples from dictionaries
        examples = self._get_examples()
        examples_text = self._format_examples(examples)
        
        return f"""คุณเป็นผู้เชี่ยวชาญด้านการแก้ไขข้อความจากระบบ Speech-to-Text สำหรับบทสนทนาทางการแพทย์ภาษาไทย

🎯 หน้าที่หลักของคุณ:
1. แก้ไขคำที่ Speech-to-Text เข้าใจผิดหรือสะกดผิด
2. แก้ไขคำศัพท์ทางการแพทย์ให้ถูกต้อง
3. แก้ไขคำทั่วไปที่มักเข้าใจผิด
4. **เก็บความหมายและเจตนาของผู้พูดไว้ทั้งหมด**

✅ สิ่งที่ควรทำ:
- แก้คำที่สะกดผิดหรือเข้าใจผิดจากเสียง
- แก้คำศัพท์การแพทย์ให้ถูกต้องตามมาตรฐาน
- แก้ไวยากรณ์ที่ผิดพลาดชัดเจน
- รักษาน้ำเสียงและความเป็นกันเองของผู้พูด

❌ สิ่งที่ห้ามทำ:
- **ห้าม**เพิ่มข้อมูลใหม่ที่ผู้พูดไม่ได้พูด
- **ห้าม**ลบหรือตัดข้อมูลที่ผู้พูดพูด
- **ห้าม**เปลี่ยนโครงสร้างประโยคมากเกินไป
- **ห้าม**เปลี่ยนความหมายหรือเจตนาของผู้พูด
- **ห้าม**ทำให้ภาษาเป็นทางการจนเกินไป

📚 ข้อมูลอ้างอิงจากพจนานุกรม:

{self.medical_terms_context}

{self.common_mistakes}

{self.correction_rules}

{examples_text}

⚠️ สำคัญมาก:
- ตอบเฉพาะข้อความที่แก้ไขแล้ว
- **ห้าม**อธิบายหรือเพิ่มคำอื่นใด
- ถ้าข้อความถูกต้องแล้ว ให้ตอบข้อความเดิมทุกประการ"""

    def _get_examples(self) -> List[Dict]:
        """Get examples from dictionaries"""
        examples = []
        
        # Get examples from medical dictionary
        medical_examples = self.medical_dictionary.get('examples', [])
        examples.extend(medical_examples)
        
        # Get examples from everyday dictionary
        everyday_examples = self.everyday_dictionary.get('examples', [])
        examples.extend(everyday_examples)
        
        return examples
    
    def _format_examples(self, examples: List[Dict]) -> str:
        """Format examples for the prompt"""
        if not examples:
            return ""
        
        text = "\n📝 ตัวอย่างการแก้ไขจากพจนานุกรม:\n\n"
        for i, example in enumerate(examples[:10], 1):  # Limit to 10 examples
            input_text = example.get('input', example.get('wrong', ''))
            output_text = example.get('output', example.get('correct', ''))
            explanation = example.get('explanation', example.get('reason', ''))
            
            text += f"Example {i}:\n"
            text += f"Input: \"{input_text}\"\n"
            text += f"Output: \"{output_text}\"\n"
            if explanation:
                text += f"เหตุผล: {explanation}\n"
            text += "\n"
        
        return text

    def _build_correction_prompt(self, text: str, context: str) -> str:
        """Build the correction prompt with context"""
        prompt = f"ข้อความที่ต้องแก้ไข: \"{text}\""
        
        if context and context.strip():
            prompt += f"\n\n📋 บริบทการสนทนา:\n{context}"
            prompt += "\n\n💡 ใช้บริบทนี้ช่วยในการตัดสินใจแก้ไขคำที่คลุมเครือ"
        
        return prompt
    
    def _identify_changes(self, original: str, corrected: str) -> list:
        """Identify what changes were made (enhanced word-level diff)"""
        original_words = original.split()
        corrected_words = corrected.split()
        
        changes = []
        
        # Simple word-by-word comparison
        if len(original_words) == len(corrected_words):
            for i, (orig, corr) in enumerate(zip(original_words, corrected_words)):
                if orig != corr:
                    changes.append(f"{orig} → {corr}")
        else:
            # If structure changed, try to identify specific changes
            original_set = set(original_words)
            corrected_set = set(corrected_words)
            
            removed = original_set - corrected_set
            added = corrected_set - original_set
            
            if removed and added:
                # Pair up likely changes
                for r in removed:
                    for a in added:
                        # Simple similarity check
                        if len(r) > 0 and len(a) > 0 and (r[0] == a[0] or r[-1] == a[-1]):
                            changes.append(f"{r} → {a}")
                            break
            
            if not changes and (removed or added):
                changes.append("โครงสร้างประโยคถูกปรับปรุง")
        
        return changes
    
    def reload_dictionaries(self):
        """Reload dictionaries from files (useful for updates without restart)"""
        logger.info("🔄 Reloading dictionaries...")
        self.medical_dictionary = self._load_json_dictionary('medical_dictionary.json')
        self.everyday_dictionary = self._load_json_dictionary('everyday_dictionary.json')
        
        self.medical_terms_context = self._build_medical_context()
        self.common_mistakes = self._build_mistakes_context()
        self.correction_rules = self._build_rules_context()
        
        logger.info("✅ Dictionaries reloaded successfully")


# Global instance
word_correction_service = WordCorrectionService()