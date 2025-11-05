"""
Enhanced Text-to-Speech Service with Natural Speech Patterns
Optimized for realistic, human-like Thai pronunciation
PRESERVES ALL ORIGINAL FEATURES + NEW NATURAL SPEECH ENHANCEMENTS
"""

import os
import base64
import re
from typing import Literal, Optional, Dict, Any
from io import BytesIO
from openai import OpenAI
from dotenv import load_dotenv

VoiceType = Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

class EnhancedTTSService:
    """Enhanced TTS service with natural speech patterns"""
    
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
                "child": "nova",
                "young": "nova",
                "adult": "nova",
                "elderly": "shimmer"
            },
            "male": {
                "child": "nova",
                "young": "echo",
                "adult": "onyx",
                "elderly": "fable"
            },
            "default": "nova"
        }
        
        self.default_model = "gpt-4o-mini-tts"
        self.default_speed = 1
    
    def _extract_age_category(self, age_data: Any) -> str:
        """Extract age category from patient info"""
        try:
            if isinstance(age_data, dict):
                age = int(age_data.get('value', 0))
            elif isinstance(age_data, str):
                age = int(''.join(filter(str.isdigit, age_data)))
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
            return "adult"
    
    def _get_actual_age(self, age_data: Any) -> int:
        """Get actual age as integer"""
        try:
            if isinstance(age_data, dict):
                return int(age_data.get('value', 0))
            elif isinstance(age_data, str):
                return int(''.join(filter(str.isdigit, age_data)))
            else:
                return int(age_data)
        except:
            return 0
    
    def _select_voice_for_patient(self, patient_info: Dict[str, Any]) -> VoiceType:
        """Select appropriate voice based on patient demographics"""
        age_data = patient_info.get('age')
        age = self._get_actual_age(age_data)
        age_category = self._extract_age_category(age_data) if age_data else "adult"
        
        # Child patient (<12 years) = Mother speaks
        if age < 12:
            print(f"👶 [SPECIAL] Child patient ({age} years) - Mother speaks (nova voice)")
            return "nova"
        
        # Extract gender
        raw_gender = patient_info.get('sex', '')
        gender_lower = str(raw_gender).lower()
        
        if 'female' in gender_lower or 'หญิง' in gender_lower or 'ผู้หญิง' in gender_lower or 'f' == gender_lower:
            gender = "female"
        elif 'male' in gender_lower or 'ชาย' in gender_lower or 'ผู้ชาย' in gender_lower or 'm' == gender_lower:
            gender = "male"
        else:
            gender = "default"
        
        selected_voice = self.voice_profiles.get(gender, self.voice_profiles["default"])
        if isinstance(selected_voice, dict):
            selected_voice = selected_voice[age_category]
        
        print(f"🎤 Selected voice: {selected_voice} (Gender: {gender}, Age: {age})")
        return selected_voice
    
    def _number_to_thai_words(self, num_str: str) -> str:
        """
        Convert number string to Thai words
        
        Examples:
        - "6" → "หก"
        - "10" → "สิบ"
        - "25" → "ยี่สิบห้า"
        - "100" → "หนึ่งร้อย"
        """
        try:
            num = int(num_str)
        except:
            return num_str
        
        if num == 0:
            return "ศูนย์"
        
        ones = ['', 'หนึ่ง', 'สอง', 'สาม', 'สี่', 'ห้า', 'หก', 'เจ็ด', 'แปด', 'เก้า']
        
        if num < 10:
            return ones[num]
        
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
        
        if num < 1000:
            hundreds = num // 100
            remainder = num % 100
            
            result = ones[hundreds] + "ร้อย"
            if remainder > 0:
                result += self._number_to_thai_words(str(remainder))
            
            return result
        
        if num < 10000:
            thousands = num // 1000
            remainder = num % 1000
            
            result = ones[thousands] + "พัน"
            if remainder > 0:
                result += self._number_to_thai_words(str(remainder))
            
            return result
        
        return num_str
    
    def _convert_symbols_to_thai(self, text: str) -> str:
        """
        Convert symbols and numbers to Thai words for daily life contexts
        
        Medical/Daily Life Contexts:
        1. Number ranges (อายุ 6-7 ปี → หก ถึง เจ็ด ปี)
        2. Time expressions (10:30 → สิบโมงครึ่ง)
        3. Percentages (80% → แปดสิบ เปอร์เซ็นต์)
        4. Dates (1/1 → หนึ่ง มกราคม)
        5. Common symbols (&, @, #)
        """
        import re
        
        result = text
        
        # 1. Handle number ranges (always "ถึง" for medical contexts)
        def replace_number_range(match):
            num1 = match.group(1)
            num2 = match.group(2)
            
            # Convert numbers to Thai
            thai_num1 = self._number_to_thai_words(num1)
            thai_num2 = self._number_to_thai_words(num2)
            
            # Medical context: always use "ถึง" (range)
            # Examples: อายุ 6-7 ปี, ปวดมา 1-2 วัน, อุณหภูมิ 37-38 องศา
            return f"{thai_num1} ถึง {thai_num2}"
        
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
            elif minute == 15:
                return f"{hour_thai}โมงสิบห้านาที"
            elif minute == 45:
                return f"{hour_thai}โมงสี่สิบห้านาที"
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
        
        # 4. Handle dates with month names (1/1, 25/12)
        def replace_date(match):
            day = match.group(1)
            month = match.group(2)
            context = text[max(0, match.start()-15):match.start()].lower()
            
            # Check if it's a date context
            if any(word in context for word in ['วันที่', 'เมื่อ', 'วัน', 'ตั้งแต่']):
                thai_day = self._number_to_thai_words(day)
                
                # Month mapping
                month_names = {
                    '1': 'มกราคม', '2': 'กุมภาพันธ์', '3': 'มีนาคม',
                    '4': 'เมษายน', '5': 'พฤษภาคม', '6': 'มิถุนายน',
                    '7': 'กรกฎาคม', '8': 'สิงหาคม', '9': 'กันยายน',
                    '10': 'ตุลาคม', '11': 'พฤศจิกายน', '12': 'ธันวาคม'
                }
                
                thai_month = month_names.get(month, month)
                return f"{thai_day} {thai_month}"
            else:
                # Not a date - could be fraction, keep as is
                return match.group(0)
        
        result = re.sub(r'(\d{1,2})/(\d{1,2})', replace_date, result)
        
        # 5. Handle common symbols used in daily conversation
        result = result.replace(' & ', ' และ ')
        result = result.replace(' @ ', ' ที่ ')
        result = result.replace(' # ', ' หมายเลข ')
        
        return result
    
    def _add_natural_pauses(self, text: str) -> str:
        """
        Add natural pauses and breathing points for more realistic speech
        Makes speech sound less robotic by adding strategic pauses
        """
        # Add SHORT pause (comma) after connecting words for natural flow
        text = re.sub(r'(แล้ว|ก็|เลย)(\s+)', r'\1, ', text)
        
        # Add THINKING pause (ellipsis) after question words
        text = re.sub(r'(อะไร|ยังไง|ทำไม|เมื่อไหร่|ที่ไหน)(\s+)', r'\1... ', text)
        
        # Add pause before contrast/explanation words
        text = re.sub(r'(\s+)(แต่|แต่ว่า|เพราะว่า|เพราะ|ถ้า|ถ้าหาก|เนื่องจาก)', r'... \2', text)
        
        # Add EMPHASIS pause before emotional/important words
        emotional_words = ['เจ็บ', 'ปวด', 'เหนื่อย', 'วิตก', 'กังวล', 'กลัว', 'ดีใจ', 'แย่', 'ร้าย', 'หนัก']
        for word in emotional_words:
            # Only add pause if not already preceded by punctuation
            text = re.sub(f'(?<![.,!?…])(\s+)({word})', r', \2', text, flags=re.IGNORECASE, count=1)
        
        # Add pause after listing words
        text = re.sub(r'(ทั้ง|และ|กับ|หรือ)(\s+)', r'\1, ', text)
        
        return text
    
    def _add_emotional_inflection(self, text: str, patient_info: Dict[str, Any]) -> str:
        """
        Add subtle textual cues for emotional inflection based on symptoms
        Makes speech sound more expressive and human-like
        """
        chief_complaint = patient_info.get('chief_complaint', '').lower()
        
        # Pain/discomfort -> add hesitation and emphasis
        if any(word in chief_complaint for word in ['ปวด', 'เจ็บ', 'pain', 'ache']):
            # Add "มาก" or "จัง" to emphasize pain
            text = re.sub(r'(ปวด|เจ็บ)(?!\s*(มาก|จัง|นัก|เลย))', r'\1มาก', text, count=1)
            # Add hesitation before describing pain
            text = re.sub(r'(ปวด|เจ็บ)', r'ค่อนข้าง\1', text, count=1)
        
        # Fatigue -> add tiredness markers
        if any(word in chief_complaint for word in ['เหนื่อย', 'อ่อนเพลิย', 'เพลีย', 'tired', 'fatigue']):
            text = re.sub(r'(เหนื่อย|อ่อนเพลิย)(?!\s*(มาก|จัง|เลย))', r'\1มาก', text, count=1)
        
        # Anxiety/worry -> add worry markers
        if any(word in chief_complaint for word in ['วิตก', 'กังวล', 'กลัว', 'anxiety', 'worried']):
            text = re.sub(r'(วิตก|กังวล|กลัว)(?!\s*(มาก|จัง))', r'ค่อนข้าง\1', text, count=1)
        
        # Fever -> add concern tone
        if any(word in chief_complaint for word in ['ไข้', 'fever', 'temperature']):
            text = re.sub(r'(ไข้|ร้อน)(?!\s*(สูง|มาก))', r'\1สูง', text, count=1)
        
        # Nausea/vomiting -> add discomfort
        if any(word in chief_complaint for word in ['คลื่นไส้', 'อาเจียน', 'nausea', 'vomit']):
            text = re.sub(r'(คลื่นไส้|อาเจียน)', r'\1บ่อย', text, count=1)
        
        return text
    
    def _add_conversational_fillers(self, text: str, speaker_role: str, age_category: str) -> str:
        """
        Add natural conversational fillers for human-like speech
        Different fillers based on speaker role and age
        """
        # Don't add fillers to very short responses
        if len(text.split()) < 6:
            return text
        
        sentences = text.split('. ')
        enhanced_sentences = []
        
        for i, sentence in enumerate(sentences):
            words = sentence.split()
            
            # Add thinking pause at beginning of first sentence (if long enough)
            if i == 0 and len(words) > 10:
                if speaker_role == 'mother':
                    # Mother: more thoughtful, caring tone
                    fillers = ['อืม...', 'ก็...', 'อ้อ...']
                    sentence = fillers[i % len(fillers)] + ' ' + sentence
                elif age_category == 'elderly':
                    # Elderly: slower, more deliberate
                    fillers = ['เอ่อ...', 'อืม...', 'ก็นะ...']
                    sentence = fillers[i % len(fillers)] + ' ' + sentence
                elif age_category == 'young':
                    # Young: casual, quick
                    fillers = ['เอ่อ', 'อืม', 'ก็']
                    sentence = fillers[i % len(fillers)] + ' ' + sentence
                else:
                    # Adult: moderate
                    fillers = ['เอ่อ...', 'อืม...']
                    sentence = fillers[i % len(fillers)] + ' ' + sentence
            
            # Add natural connectors between sentences (not every sentence)
            if i > 0 and i < len(sentences) - 1 and len(words) > 6:
                # Only add connector every other sentence to avoid monotony
                if i % 2 == 0:
                    if speaker_role == 'mother':
                        connectors = ['แล้วก็', 'ส่วน', 'อีกอย่าง']
                        sentence = connectors[i % len(connectors)] + '... ' + sentence
                    elif age_category == 'elderly':
                        connectors = ['แล้วก็', 'อีกอย่างหนึ่ง', 'แล้วนะ']
                        sentence = connectors[i % len(connectors)] + ' ' + sentence
                    else:
                        connectors = ['แล้วก็', 'แล้ว', 'อีกอย่าง']
                        sentence = connectors[i % len(connectors)] + ' ' + sentence
            
            enhanced_sentences.append(sentence)
        
        return '. '.join(enhanced_sentences)
    
    def _vary_sentence_endings(self, text: str, patient_info: Dict[str, Any], age_category: str) -> str:
        """
        Vary sentence endings for more natural flow
        Uses different patterns to avoid monotone repetition
        """
        gender = patient_info.get('sex', '').lower()
        age = self._get_actual_age(patient_info.get('age'))
        
        # Determine polite particle
        if age < 12:
            particle = 'ค่ะ'  # Mother speaking
        elif 'female' in gender or 'หญิง' in gender:
            particle = 'ค่ะ'
        else:
            particle = 'ครับ'
        
        # Common Thai sentence ending particles (expanded list)
        ending_particles = ('ค่ะ', 'ครับ', 'นะ', 'เลย', 'น่ะ', 'จ้า', 'จ๊ะ', 'นะคะ', 'นะครับ', 'ค่า', 'ค่ะ', 'ขอรับ')
        
        sentences = text.split('. ')
        varied_sentences = []
        
        # Create varied ending patterns based on age/role
        if age < 12:  # Mother speaking
            ending_patterns = [particle, 'นะคะ', particle, 'น่ะ', particle]
        elif age_category == 'elderly':
            ending_patterns = [particle, 'นะ', particle, 'เลย', particle]
        elif age_category == 'young':
            ending_patterns = ['น่ะ', particle, 'นะ', particle, 'เลย']
        else:  # Adult
            ending_patterns = [particle, 'นะ', particle, 'น่ะ', particle]
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            
            # Check if sentence already has ending particle
            has_ending = any(sentence.endswith(p) for p in ending_particles)
            
            # Skip if already has ending
            if has_ending:
                varied_sentences.append(sentence)
                continue
            
            # Only add ending if sentence is substantial (more than 2 words)
            if len(sentence.split()) <= 2:
                varied_sentences.append(sentence)
                continue
            
            # Use pattern rotation instead of position-based
            ending = ending_patterns[i % len(ending_patterns)]
            sentence += ' ' + ending
            
            varied_sentences.append(sentence)
        
        return '. '.join(varied_sentences)
    
    def _optimize_text_for_thai_tts(self, text: str, patient_info: Dict[str, Any]) -> str:
        """
        Comprehensive text optimization for natural, human-like Thai speech
        
        Processing order:
        1. Convert symbols to Thai words
        2. Add emotional inflection based on symptoms
        3. Add natural pauses and breathing points
        4. Add conversational fillers
        5. Vary sentence endings
        6. Clean up formatting
        """
        if not text or not text.strip():
            return text
        
        age = self._get_actual_age(patient_info.get('age'))
        age_category = self._extract_age_category(patient_info.get('age'))
        speaker_role = 'mother' if age < 12 else 'patient'
        
        # 1. Convert symbols to Thai words
        optimized = self._convert_symbols_to_thai(text)
        
        # 2. Add emotional inflection FIRST (before pauses)
        optimized = self._add_emotional_inflection(optimized, patient_info)
        
        # 3. Add natural pauses and breathing points
        optimized = self._add_natural_pauses(optimized)
        
        # 4. Add conversational fillers
        optimized = self._add_conversational_fillers(optimized, speaker_role, age_category)
        
        # 5. Vary sentence endings
        optimized = self._vary_sentence_endings(optimized, patient_info, age_category)
        
        # 6. Clean up excessive punctuation
        optimized = re.sub(r'\.{4,}', '...', optimized)  # Max 3 dots
        optimized = re.sub(r',\s*,', ',', optimized)  # Remove double commas
        optimized = re.sub(r'\s+', ' ', optimized)  # Normalize spaces
        optimized = re.sub(r'\.\.\.\s*\.\.\.', '...', optimized)  # Remove double ellipsis
        
        # Handle special cases for child patients (mother speaking)
        if age < 12:
            # Mother speaking - ensure maternal perspective
            optimized = optimized.replace('หนู', 'ลูก')  # When mother talks about child
        
        print(f"🎭 [TTS OPTIMIZATION] Enhanced for natural speech")
        if text != optimized:
            print(f"   Original: {text[:100]}...")
            print(f"   Enhanced: {optimized[:100]}...")
        
        return optimized
    
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
        
        # Auto-select voice
        if voice is None:
            voice = self._select_voice_for_patient(patient_info)
        
        model = model or self.default_model
        speed = speed or self.default_speed
        
        # Adjust speed for natural speech
        age = self._get_actual_age(patient_info.get('age'))
        
        if age < 12:
            # Mother speaking - warm, moderate pace
            speed = max(0.88, min(speed, 0.98))
        else:
            age_category = self._extract_age_category(patient_info.get('age'))
            if age_category == "elderly":
                speed = max(0.80, speed - 0.10)  # Slower, more deliberate
            elif age_category == "young":
                speed = min(1.08, speed + 0.08)  # Natural energetic pace
            else:
                speed = max(0.92, min(speed, 1.02))  # Moderate adult pace
        
        # Optimize text for natural, human-like speech
        final_text = self._optimize_text_for_thai_tts(text, patient_info)
        
        # Validate speed
        if not 0.25 <= speed <= 4.0:
            raise ValueError("Speed must be between 0.25 and 4.0")
        
        try:
            print(f"🎤 Generating natural TTS: voice={voice}, speed={speed}x")
            
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=final_text,
                speed=speed,
                response_format=output_format
            )
            
            print(f"✅ Natural TTS generation successful")
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
        """Convert text to speech with context and return as base64"""
        audio_bytes = self.text_to_speech_with_context(
            text, patient_info, case_metadata, voice,
            model, speed, output_format, use_personality_prompt
        )
        return base64.b64encode(audio_bytes).decode('utf-8')
    
    # Backward compatibility methods
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
        """Get available voice options"""
        return {
            "alloy": "Neutral, versatile voice",
            "echo": "Male voice, clear and articulate (young male)",
            "fable": "British accent, expressive (elderly male)",
            "onyx": "Deep male voice, authoritative (adult male)",
            "nova": "Female voice, warm and friendly (young female, or mother)",
            "shimmer": "Female voice, soft and gentle (elderly female)"
        }
    
    def get_voice_profiles(self) -> dict:
        """Get voice profile mapping"""
        return self.voice_profiles
    
    def get_speaker_role(self, patient_info: Dict[str, Any]) -> str:
        """Get speaker role (mother/patient)"""
        age = self._get_actual_age(patient_info.get('age'))
        return 'mother' if age < 12 else 'patient'

# Create singleton instance
enhanced_tts_service = EnhancedTTSService()