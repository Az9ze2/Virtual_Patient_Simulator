"""
Enhanced Text-to-Speech Service with Patient Context
Generates dynamic voice personality based on patient information
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
    
    def _select_voice_for_patient(self, patient_info: Dict[str, Any]) -> VoiceType:
        """
        Select appropriate voice based on patient demographics
        
        Args:
            patient_info: Patient information dictionary
        
        Returns:
            Selected voice type
        """
        print(f"🔍 [DEBUG] Raw patient_info received: {patient_info}")
        
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
        
        # Extract age category
        age_data = patient_info.get('age')
        print(f"🔍 [DEBUG] Raw age data: {age_data}")
        age_category = self._extract_age_category(age_data) if age_data else "adult"
        print(f"🔍 [DEBUG] Age category: {age_category}")
        
        # Select voice based on profile
        if gender in ["female", "male"]:
            selected_voice = self.voice_profiles[gender][age_category]
            print(f"✅ [DEBUG] Voice selected from profile: {selected_voice}")
        else:
            selected_voice = self.voice_profiles["default"]
            print(f"⚠️ [DEBUG] Using default voice: {selected_voice}")
        
        print(f"🎭 Patient Profile Summary: Gender={gender}, Age Category={age_category}")
        print(f"🎤 Final Selected Voice: {selected_voice}")
        print(f"=" * 60)
        
        return selected_voice
    
    def _generate_personality_prompt(
        self, 
        text: str,
        patient_info: Dict[str, Any],
        case_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate enhanced prompt with personality context for TTS
        
        Args:
            text: Original text to speak
            patient_info: Patient information
            case_metadata: Case metadata for additional context
        
        Returns:
            Enhanced prompt with personality instructions
        """
        # Extract patient details
        name = patient_info.get('name', 'ผู้ป่วย')
        age_data = patient_info.get('age')
        gender = patient_info.get('sex', '')
        chief_complaint = patient_info.get('chief_complaint', '')
        
        # Parse age
        age_category = self._extract_age_category(age_data)
        
        # Build personality context
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
        
        # Build enhanced prompt
        personality_desc = ", ".join(personality_traits)
        
        enhanced_prompt = f"""[บทบาท: {name} - ผู้ป่วย{gender} อายุ {age_data}]
[ลักษณะ: {personality_desc}]
[โปรดพูดด้วยลักษณะของบุคคลนี้โดยเฉพาะ ใช้น้ำเสียง อารมณ์ และจังหวะการพูดที่เหมาะสม]

{text}"""
        
        return enhanced_prompt
    
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
        
        # Adjust speed based on age category
        if patient_info:
            age_category = self._extract_age_category(patient_info.get('age'))
            if age_category == "elderly":
                speed = max(0.6, speed - 0.1)  # Slower for elderly
            elif age_category == "young":
                speed = min(1.1, speed + 0.1)  # Slightly faster for young
        
        # ⚠️ IMPORTANT: OpenAI TTS doesn't support personality prompts like ChatGPT
        # The personality/emotion must be conveyed through:
        # 1. Voice selection (we do this automatically)
        # 2. Speech speed adjustment (we do this based on age)
        # 3. The actual text content itself
        
        # We only send the actual patient response text, NOT the personality instructions
        final_text = text
        
        if use_personality_prompt and patient_info:
            # Log the personality context for debugging, but don't send it to TTS
            personality_context = self._generate_personality_prompt(
                text, patient_info, case_metadata
            )
            print(f"🎭 Personality Context (for reference only, NOT sent to TTS):")
            print(f"   {personality_context[:200]}...")
            print(f"📢 Actual text sent to TTS: {text[:100]}...")
        
        # Validate speed
        if not 0.25 <= speed <= 4.0:
            raise ValueError("Speed must be between 0.25 and 4.0")
        
        try:
            print(f"🎤 Generating TTS: voice={voice}, speed={speed}x, format={output_format}")
            
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=final_text,  # Only send the actual response text
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
            "nova": "Female voice, warm and friendly (young female)",
            "shimmer": "Female voice, soft and gentle (adult/elderly female)"
        }
    
    def get_voice_profiles(self) -> dict:
        """Get voice profile mapping for documentation"""
        return self.voice_profiles

# Create singleton instance
enhanced_tts_service = EnhancedTTSService()