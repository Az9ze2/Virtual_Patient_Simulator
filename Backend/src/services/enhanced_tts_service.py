"""
Enhanced Text-to-Speech Service with Patient Context
Generates dynamic voice personality based on patient information
OPTIMIZED for natural Thai pronunciation and child patient handling
"""

import os
import base64
from typing import Literal, Optional, Dict, Any
from io import BytesIO
from openai import OpenAI
from dotenv import load_dotenv

# Voice types available in OpenAI TTS
VoiceType = Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

class EnhancedTTSService:
    """Enhanced TTS service with patient-aware voice generation"""
    
    def __init__(self):
        """Initialize TTS service with OpenAI client"""
        load_dotenv()
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Voice mapping based on gender and age
        self.voice_profiles = {
            "female": {
                "child": "nova",  # For mother of child
                "young": "nova",
                "adult": "nova",
                "elderly": "shimmer"
            },
            "male": {
                "child": "nova",  # For mother of child (overridden)
                "young": "echo",
                "adult": "onyx",
                "elderly": "fable"
            },
            "default": "nova"
        }
        
        # Default configuration
        self.default_model = "gpt-4o-mini-tts"
        self.default_speed = 1
    

    def _extract_age_category(self, age_data: Any) -> str:
        """
        Extract age category from patient info
        
        Args:
            age_data: Age information (can be dict with value/unit or number)
        
        Returns:
            Age category:"child" (<12) "young" (12-30), "adult" (30-60), "elderly" (>60)
        """
        try:
            # Handle dict format: {"value": 45, "unit": "years"}
            if isinstance(age_data, dict):
                age = int(age_data.get('value', 0))
            # Handle string format: "45 years"
            elif isinstance(age_data, str):
                age = int(''.join(filter(str.isdigit, age_data)))
            # Handle direct number
            else:
                age = int(age_data)
            
            if age < 12:
                return "child"
            elif age >= 12 and age < 30:
                return "young"
            elif age <= 60:
                return "adult"
            else:
                return "elderly"
        except:
            return "adult"  # Default to adult if parsing fails
    
    def _get_actual_age(self, age_data: Any) -> int:
        """
        Get actual age as integer
        
        Args:
            age_data: Age information
            
        Returns:
            Age as integer
        """
        try:
            if isinstance(age_data, dict):
                return int(age_data.get('value', 0))
            elif isinstance(age_data, str):
                return int(''.join(filter(str.isdigit, age_data)))
            else:
                return int(age_data)
        except:
            return 0
    
    def _is_child_patient(self, patient_info: Dict[str, Any]) -> bool:
        """
        Check if patient is a child (under 12 years old)
        
        Args:
            patient_info: Patient information dictionary
            
        Returns:
            True if patient is under 12 years old
        """
        age_data = patient_info.get('age')
        if not age_data:
            return False
        
        age = self._get_actual_age(age_data)
        return age < 12
    
    def _select_voice_for_patient(self, patient_info: Dict[str, Any]) -> VoiceType:
        """
        Select appropriate voice based on patient demographics
        Special handling: If patient is child (<12 years), always use mother's voice (nova)
        
        Args:
            patient_info: Patient information dictionary
        
        Returns:
            Selected voice type
        """
        print(f"🔍 [DEBUG] Raw patient_info received: {patient_info}")
        
        # Extract age data first
        age_data = patient_info.get('age')
        print(f"🔍 [DEBUG] Raw age data: {age_data}")
        age = self._get_actual_age(age_data)
        age_category = self._extract_age_category(age_data) if age_data else "adult"
        print(f"🔍 [DEBUG] Age: {age}, Age category: {age_category}")
        
        # 🎯 SPECIAL CONDITION: Child patient (<12 years) = Mother speaks
        if age < 12:
            print(f"👶 [SPECIAL] Patient is a child ({age} years old)")
            print(f"👩 [SPECIAL] Mother will speak for the child - using 'nova' voice")
            print(f"=" * 60)
            return "nova"  # Always use female voice for mother
        
        # Extract gender (normalize to lowercase)
        raw_gender = patient_info.get('sex', '')
        print(f"🔍 [DEBUG] Raw gender value: '{raw_gender}' (type: {type(raw_gender)})")
        
        gender_lower = str(raw_gender).lower()
        print(f"🔍 [DEBUG] Gender lowercase: '{gender_lower}'")
        
        # Check for female indicators
        if 'female' in gender_lower or 'หญิง' in gender_lower or 'ผู้หญิง' in gender_lower or 'f' == gender_lower:
            gender = "female"
            print(f"✅ [DEBUG] Detected as FEMALE")
        # Check for male indicators  
        elif 'male' in gender_lower or 'ชาย' in gender_lower or 'ผู้ชาย' in gender_lower or 'm' == gender_lower:
            gender = "male"
            print(f"✅ [DEBUG] Detected as MALE")
        else:
            gender = "default"
            print(f"⚠️ [DEBUG] Gender not detected, using DEFAULT (nova)")
            print(f"⚠️ [DEBUG] Gender value was: '{raw_gender}'")
        
        # Select voice based on profile
        if gender in ["female", "male"]:
            selected_voice = self.voice_profiles[gender][age_category]
            print(f"✅ [DEBUG] Voice selected from profile: {selected_voice}")
        else:
            selected_voice = self.voice_profiles["default"]
            print(f"⚠️ [DEBUG] Using default voice: {selected_voice}")
        
        print(f"🎭 Patient Profile Summary: Gender={gender}, Age={age}, Category={age_category}")
        print(f"🎤 Final Selected Voice: {selected_voice}")
        print(f"=" * 60)
        
        return selected_voice
    
    def _convert_symbols_to_thai(self, text: str) -> str:
        """
        Convert symbols and numbers to Thai words based on context
        
        Handles:
        1. Number ranges (6-7 → หก ถึง เจ็ด or หก ลบ เจ็ด)
        2. Math operations (+, -, ×, ÷)
        3. Common symbols (%, /, @, #)
        4. Time expressions (10:30 → สิบโมงครึ่ง)
        5. Dates (1/1/2024 → หนึ่ง มกราคม พ.ศ. สองพันยี่สิบสี่)
        
        Args:
            text: Text with symbols
            
        Returns:
            Text with symbols converted to Thai words
        """
        import re
        
        # Thai number words
        thai_numbers = {
            '0': 'ศูนย์', '1': 'หนึ่ง', '2': 'สอง', '3': 'สาม', '4': 'สี่',
            '5': 'ห้า', '6': 'หก', '7': 'เจ็ด', '8': 'แปด', '9': 'เก้า',
            '10': 'สิบ'
        }
        
        result = text
        
        # 1. Handle number ranges and dashes
        # Context: "อายุ 6-7 ปี", "6-7 วัน", "อุณหภูมิ 37-38 องศา"
        # Pattern: number-number with optional spaces
        def replace_number_range(match):
            num1 = match.group(1)
            num2 = match.group(2)
            context_before = text[max(0, match.start()-20):match.start()].lower()
            context_after = text[match.end():min(len(text), match.end()+20)].lower()
            
            # Check if it's a range context (use "ถึง")
            range_keywords = ['อายุ', 'ปี', 'วัน', 'เดือน', 'ครั้ง', 'องศา', 'เซนติเมตร', 
                            'กิโลกรัม', 'ชั่วโมง', 'นาที', 'มิลลิลิตร', 'กรัม', 'เม็ด']
            
            is_range = any(keyword in context_before + context_after for keyword in range_keywords)
            
            # Convert numbers to Thai
            thai_num1 = self._number_to_thai_words(num1)
            thai_num2 = self._number_to_thai_words(num2)
            
            if is_range:
                return f"{thai_num1} ถึง {thai_num2}"
            else:
                # Math context - use "ลบ"
                return f"{thai_num1} ลบ {thai_num2}"
        
        # Match patterns like "6-7", "6 - 7", "10-20"
        result = re.sub(r'(\d+)\s*-\s*(\d+)', replace_number_range, result)
        
        # 2. Handle time expressions (10:30, 14:00)
        def replace_time(match):
            hour = int(match.group(1))
            minute = int(match.group(2))
            
            hour_thai = self._number_to_thai_words(str(hour))
            
            if minute == 0:
                return f"{hour_thai}โมงตรง"
            elif minute == 30:
                return f"{hour_thai}โมงครึ่ง"
            else:
                minute_thai = self._number_to_thai_words(str(minute))
                return f"{hour_thai}โมง{minute_thai}นาที"
        
        result = re.sub(r'(\d{1,2}):(\d{2})', replace_time, result)
        
        # 3. Handle percentage (50%, 80%)
        def replace_percentage(match):
            num = match.group(1)
            thai_num = self._number_to_thai_words(num)
            return f"{thai_num} เปอร์เซ็นต์"
        
        result = re.sub(r'(\d+)\s*%', replace_percentage, result)
        
        # 4. Handle fractions and division (1/2, 3/4)
        def replace_fraction(match):
            num = match.group(1)
            den = match.group(2)
            context = text[max(0, match.start()-10):match.start()].lower()
            
            # Check if it's a date (1/1, 12/25)
            if any(word in context for word in ['วันที่', 'เมื่อ', 'วัน']):
                # It's a date, keep as numbers
                return match.group(0)
            
            thai_num = self._number_to_thai_words(num)
            thai_den = self._number_to_thai_words(den)
            return f"{thai_num} ส่วน {thai_den}"
        
        result = re.sub(r'(\d+)/(\d+)', replace_fraction, result)
        
        # 5. Handle mathematical operations
        result = result.replace(' + ', ' บวก ')
        result = result.replace(' × ', ' คูณ ')
        result = result.replace(' ÷ ', ' หาร ')
        result = result.replace(' = ', ' เท่ากับ ')
        result = result.replace(' < ', ' น้อยกว่า ')
        result = result.replace(' > ', ' มากกว่า ')
        result = result.replace(' ≤ ', ' น้อยกว่าหรือเท่ากับ ')
        result = result.replace(' ≥ ', ' มากกว่าหรือเท่ากับ ')
        
        # 6. Handle common symbols
        result = result.replace(' @ ', ' แอด ')
        result = result.replace(' # ', ' หมายเลข ')
        result = result.replace(' & ', ' และ ')
        
        return result
    
    def _number_to_thai_words(self, num_str: str) -> str:
        """
        Convert number string to Thai words
        
        Examples:
        - "6" → "หก"
        - "10" → "สิบ"
        - "25" → "ยี่สิบห้า"
        - "100" → "หนึ่งร้อย"
        
        Args:
            num_str: Number as string
            
        Returns:
            Thai word representation
        """
        try:
            num = int(num_str)
        except:
            return num_str
        
        if num == 0:
            return "ศูนย์"
        
        # Basic digits
        ones = ['', 'หนึ่ง', 'สอง', 'สาม', 'สี่', 'ห้า', 'หก', 'เจ็ด', 'แปด', 'เก้า']
        
        # Handle 1-9
        if num < 10:
            return ones[num]
        
        # Handle 10-99
        if num < 100:
            tens = num // 10
            ones_digit = num % 10
            
            result = ""
            if tens == 1:
                result = "สิบ"
            elif tens == 2:
                result = "ยี่สิบ"
            else:
                result = ones[tens] + "สิบ"
            
            if ones_digit == 1 and tens > 0:
                result += "เอ็ด"
            elif ones_digit > 0:
                result += ones[ones_digit]
            
            return result
        
        # Handle 100-999
        if num < 1000:
            hundreds = num // 100
            remainder = num % 100
            
            result = ones[hundreds] + "ร้อย"
            if remainder > 0:
                result += self._number_to_thai_words(str(remainder))
            
            return result
        
        # Handle 1000+
        if num < 10000:
            thousands = num // 1000
            remainder = num % 1000
            
            result = ones[thousands] + "พัน"
            if remainder > 0:
                result += self._number_to_thai_words(str(remainder))
            
            return result
        
        # For larger numbers, just return the original
        return num_str
    
    def _optimize_text_for_thai_tts(self, text: str, patient_info: Dict[str, Any]) -> str:
        """
        Optimize Thai text for more natural TTS pronunciation
        
        Key optimizations:
        1. Convert symbols to Thai words based on context
        2. Add spacing for better word boundaries
        3. Add punctuation for natural pauses
        4. Handle special cases for child patients
        
        Args:
            text: Original Thai text
            patient_info: Patient information for context
            
        Returns:
            Optimized text for TTS
        """
        if not text or not text.strip():
            return text
        
        # 1. Convert symbols to Thai words (FIRST - before other processing)
        optimized = self._convert_symbols_to_thai(text)
        
        # 2. Ensure proper spacing after punctuation for natural pauses
        optimized = optimized.replace('คะ ', 'คะ ')  # Already good
        optimized = optimized.replace('ครับ ', 'ครับ ')  # Already good
        optimized = optimized.replace('ค่ะ ', 'ค่ะ ')  # Already good
        
        # 3. Add slight pause markers for very long sentences (every 15-20 words)
        words = optimized.split()
        if len(words) > 20:
            # Insert natural breaks with commas
            result = []
            for i, word in enumerate(words):
                result.append(word)
                # Add comma at natural break points (every 15-20 words)
                if (i + 1) % 18 == 0 and i < len(words) - 1:
                    # Only add if there isn't already punctuation
                    if not any(p in word for p in [',', '.', '?', '!', 'ค่ะ', 'คะ', 'ครับ']):
                        result[-1] = result[-1] + ','
            optimized = ' '.join(result)
        
        # 4. Handle special cases for child patients (mother speaking)
        age = self._get_actual_age(patient_info.get('age'))
        if age < 12:
            # Mother speaking - ensure maternal tone markers
            # Replace child's first-person with mother's perspective if needed
            optimized = optimized.replace('หนู', 'ลูก')  # When mother talks about child
        
        print(f"📝 [TTS OPTIMIZATION] Original length: {len(text)}, Optimized: {len(optimized)}")
        if text != optimized:
            print(f"   🔄 Symbols converted:")
            print(f"      Before: {text[:150]}...")
            print(f"      After:  {optimized[:150]}...")
        
        return optimized
    
    def _generate_personality_prompt(
        self, 
        text: str,
        patient_info: Dict[str, Any],
        case_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate enhanced prompt with personality context for natural Thai speech
        
        NOTE: This is for logging/reference only. OpenAI TTS doesn't support personality
        prompts directly. Natural speech is achieved through:
        1. Voice selection (automatic based on patient)
        2. Text optimization (spacing, punctuation, phrasing)
        3. Speed adjustment (age-based)
        
        Args:
            text: Original text to speak
            patient_info: Patient information
            case_metadata: Case metadata for additional context
        
        Returns:
            Enhanced context description (for logging only)
        """
        # Extract patient details
        name = patient_info.get('name', 'ผู้ป่วย')
        age_data = patient_info.get('age')
        age = self._get_actual_age(age_data)
        gender = patient_info.get('sex', '')
        chief_complaint = patient_info.get('chief_complaint', '')
        
        # Parse age category
        age_category = self._extract_age_category(age_data)
        
        # 🎯 SPECIAL CASE: Child patient
        if age < 12:
            personality_context = f"""
[บทบาท: คุณแม่ของ {name} - เด็ก{gender} อายุ {age} ปี]
[ลักษณะการพูด: คุณแม่พูดแทนลูก เป็นกังวลเรื่องอาการของลูก พูดด้วยน้ำเสียงที่แสดงความห่วงใย]

คำแนะนำสำหรับการออกเสียง:
- พูดด้วยน้ำเสียงของผู้หญิงวัยกลางคน (อายุประมาณ 30-40 ปี)
- แสดงความกังวลต่อลูกในน้ำเสียง
- ใช้คำว่า "ลูก" หรือ "น้อง" เมื่ออ้างถึงเด็ก
- น้ำเสียงอบอุ่นแต่มีความกังวล
- พูดชัดเจนและค่อนข้างช้าเพื่อให้หมอเข้าใจ

{text}
"""
            return personality_context
        
        # Build personality traits for non-child patients
        personality_traits = []
        
        # Age-based traits (Thai context)
        if age_category == "young":
            personality_traits.extend([
                "พูดจาค่อนข้างรวดเร็วและมีพลัง",
                "แสดงความกังวลได้ชัดเจน"
            ])
        elif age_category == "adult":
            personality_traits.extend([
                "พูดจาสุภาพและชัดเจน",
                "แสดงความรู้สึกพอสมควร"
            ])
        else:  # elderly
            personality_traits.extend([
                "พูดจาช้าและเน้นคำ",
                "มีความกังวลเรื่องสุขภาพ"
            ])
        
        # Gender-based traits
        if 'female' in gender.lower() or 'หญิง' in gender:
            personality_traits.append("น้ำเสียงอ่อนโยนและอบอุ่น")
        elif 'male' in gender.lower() or 'ชาย' in gender:
            personality_traits.append("น้ำเสียงมั่นคงและตรงไปตรงมา")
        
        # Symptom-based emotional tone
        if chief_complaint:
            complaint_lower = chief_complaint.lower()
            if any(word in complaint_lower for word in ['ปวด', 'เจ็บ', 'pain', 'hurt']):
                personality_traits.append("แสดงความเจ็บปวดในน้ำเสียง")
            if any(word in complaint_lower for word in ['เหนื่อย', 'tired', 'fatigue']):
                personality_traits.append("เสียงอ่อนล้าและเหนื่อยหน่าย")
            if any(word in complaint_lower for word in ['วิตกกังวล', 'anxiety', 'worried']):
                personality_traits.append("แสดงความกังวลและกระวนกระวาย")
        
        # Add case severity context if available
        if case_metadata:
            severity = case_metadata.get('difficulty_level', '')
            if severity in ['hard', 'ยาก']:
                personality_traits.append("แสดงความรู้สึกไม่สบายอย่างชัดเจน")
        
        # Build context description
        personality_desc = ", ".join(personality_traits)
        
        context = f"""
[บทบาท: {name} - ผู้ป่วย{gender} อายุ {age} ปี]
[ลักษณะ: {personality_desc}]

คำแนะนำสำหรับการออกเสียงภาษาไทยที่เป็นธรรมชาติ:
- พูดด้วยสำเนียงคนไทยกลาง (Standard Thai)
- เน้นคำสุภาษิตและคำลงท้ายที่เหมาะสม (ค่ะ/ครับ)
- จังหวะและความเร็วตามวัยและอารมณ์
- พักเสียงตามจุดหยุดที่เป็นธรรมชาติ
- ออกเสียงให้ชัดเจนโดยเฉพาะศัพท์ทางการแพทย์

{text}
"""
        
        return context
    
    def text_to_speech_with_context(
        self,
        text: str,
        patient_info: Dict[str, Any],
        case_metadata: Optional[Dict[str, Any]] = None,
        voice: Optional[VoiceType] = None,
        model: Optional[str] = None,
        speed: Optional[float] = None,
        output_format: str = "mp3",
        use_personality_prompt: bool = True
    ) -> bytes:
        """
        Convert text to speech with patient context
        
        Args:
            text: The text to convert to speech
            patient_info: Patient information for voice selection
            case_metadata: Optional case metadata for additional context
            voice: Optional voice override (if None, auto-selects based on patient)
            model: TTS model
            speed: Speech speed (0.25 to 4.0)
            output_format: Audio format
            use_personality_prompt: Whether to enhance prompt with personality
        
        Returns:
            Audio data as bytes
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Auto-select voice based on patient info if not specified
        if voice is None:
            voice = self._select_voice_for_patient(patient_info)
        
        # Use defaults if not specified
        model = model or self.default_model
        speed = speed or self.default_speed
        
        # Adjust speed based on age category and special conditions
        age = self._get_actual_age(patient_info.get('age'))
        
        if age < 12:
            # Mother speaking for child - moderate speed, clear pronunciation
            speed = max(0.85, min(speed, 0.95))
            print(f"👩 Mother speaking mode - adjusted speed to {speed}x for clarity")
        else:
            # Original age-based adjustment for patient speaking
            age_category = self._extract_age_category(patient_info.get('age'))
            if age_category == "elderly":
                speed = max(0.75, speed - 0.15)  # Slower for elderly
            elif age_category == "young":
                speed = min(1.05, speed + 0.05)  # Slightly faster for young
        
        # ⚠️ IMPORTANT: OpenAI TTS doesn't support personality prompts like ChatGPT
        # Natural speech is achieved through:
        # 1. Voice selection (we do this automatically)
        # 2. Text optimization (spacing, punctuation, natural phrasing)
        # 3. Speech speed adjustment (we do this based on age/condition)
        
        # 📝 Optimize text for natural Thai pronunciation
        final_text = self._optimize_text_for_thai_tts(text, patient_info)
        
        if use_personality_prompt and patient_info:
            # Log the personality context for debugging, but don't send it to TTS
            personality_context = self._generate_personality_prompt(
                text, patient_info, case_metadata
            )
            print(f"🎭 Personality Context (for reference only, NOT sent to TTS):")
            print(f"   {personality_context[:300]}...")
            print(f"📢 Actual text sent to TTS: {final_text[:100]}...")
        
        # Validate speed
        if not 0.25 <= speed <= 4.0:
            raise ValueError("Speed must be between 0.25 and 4.0")
        
        try:
            print(f"🎤 Generating TTS: voice={voice}, speed={speed}x, format={output_format}")
            
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=final_text,  # Optimized text with natural phrasing
                speed=speed,
                response_format=output_format
            )
            
            print(f"✅ TTS generation successful")
            return response.content
            
        except Exception as e:
            print(f"❌ TTS generation failed: {str(e)}")
            raise Exception(f"TTS generation failed: {str(e)}")
    
    def text_to_speech_base64_with_context(
        self,
        text: str,
        patient_info: Dict[str, Any],
        case_metadata: Optional[Dict[str, Any]] = None,
        voice: Optional[VoiceType] = None,
        model: Optional[str] = None,
        speed: Optional[float] = None,
        output_format: str = "mp3",
        use_personality_prompt: bool = True
    ) -> str:
        """
        Convert text to speech with context and return as base64 string
        """
        audio_bytes = self.text_to_speech_with_context(
            text, patient_info, case_metadata, voice, 
            model, speed, output_format, use_personality_prompt
        )
        return base64.b64encode(audio_bytes).decode('utf-8')
    
    # Keep original methods for backward compatibility
    def text_to_speech(
        self,
        text: str,
        voice: VoiceType = None,
        model: str = None,
        speed: float = None,
        output_format: str = "mp3"
    ) -> bytes:
        """Original method for backward compatibility"""
        voice = voice or "nova"
        model = model or self.default_model
        speed = speed or self.default_speed
        
        if not 0.25 <= speed <= 4.0:
            raise ValueError("Speed must be between 0.25 and 4.0")
        
        try:
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                speed=speed,
                response_format=output_format
            )
            return response.content
        except Exception as e:
            raise Exception(f"TTS generation failed: {str(e)}")
    
    def text_to_speech_base64(
        self,
        text: str,
        voice: VoiceType = None,
        model: str = None,
        speed: float = None,
        output_format: str = "mp3"
    ) -> str:
        """Original method for backward compatibility"""
        audio_bytes = self.text_to_speech(text, voice, model, speed, output_format)
        return base64.b64encode(audio_bytes).decode('utf-8')
    
    def get_available_voices(self) -> dict:
        """Get available voice options with descriptions"""
        return {
            "alloy": "Neutral, versatile voice",
            "echo": "Male voice, clear and articulate (young male)",
            "fable": "British accent, expressive (elderly male)",
            "onyx": "Deep male voice, authoritative (adult male)",
            "nova": "Female voice, warm and friendly (young female, or mother for children)",
            "shimmer": "Female voice, soft and gentle (adult/elderly female)"
        }
    
    def get_voice_profiles(self) -> dict:
        """Get voice profile mapping for documentation"""
        return self.voice_profiles
    
    def get_speaker_role(self, patient_info: Dict[str, Any]) -> str:
        """
        Get the speaker role based on patient information
        
        Args:
            patient_info: Patient information dictionary
            
        Returns:
            Speaker role: 'mother' for children <12, 'patient' for others
        """
        age = self._get_actual_age(patient_info.get('age'))
        return 'mother' if age < 12 else 'patient'

# Create singleton instance
enhanced_tts_service = EnhancedTTSService()