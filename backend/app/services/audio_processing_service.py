"""
Audio processing service using Gemini 2.0 Flash Audio Understanding API
"""
import os
import logging
import asyncio
import time
from typing import Optional, Dict, Any, Union
from io import BytesIO

from app.schemas.audio_schemas import AudioProcessingResult, AudioAnalysisResult
from app.config import app_settings
# from app.utils.performance import measure_execution_time  # Not needed for now

# Import Vertex AI for Gemini access
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    logging.warning("Vertex AI SDK not available. Audio processing will use mock data.")

logger = logging.getLogger(__name__)

class AudioProcessingService:
    """Service for processing audio using Gemini Audio Understanding API"""
    
    def __init__(self):
        self.project_id = app_settings.gcp_project_id
        self.location = app_settings.gcp_location or "us-central1"
        self.model_name = "gemini-2.0-flash-exp"  # Use experimental model for audio
        
        # Initialize Vertex AI if available
        if VERTEX_AI_AVAILABLE and self.project_id:
            try:
                vertexai.init(project=self.project_id, location=self.location)
                self.model = GenerativeModel(self.model_name)
                self.initialized = True
                logger.info(f"Initialized Gemini model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI: {e}")
                self.initialized = False
        else:
            self.initialized = False
            logger.warning("Running in mock mode - no Vertex AI connection")
    
    async def process_audio_input(
        self,
        audio_data: bytes,
        mime_type: str,
        language_hint: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        system_instruction: Optional[str] = None
    ) -> AudioProcessingResult:
        """
        Process audio input using Gemini Audio Understanding API
        
        Args:
            audio_data: Raw audio bytes
            mime_type: MIME type of audio (e.g., "audio/wav")
            language_hint: Expected language code (e.g., "ja" for Japanese)
            context: Additional context (device_id, location, etc.)
            system_instruction: Custom instruction for audio processing
            
        Returns:
            AudioProcessingResult with transcription and analysis
        """
        start_time = time.time()
        
        # Use mock data in test mode or if Vertex AI not available
        if app_settings.is_test_mode() or not self.initialized:
            return await self._mock_audio_processing(
                audio_data, mime_type, language_hint
            )
        
        try:
            # Default system instruction for disaster support context
            if not system_instruction:
                system_instruction = self._build_system_instruction(language_hint, context)
            
            # Create audio part for Gemini
            audio_part = Part.from_data(
                data=audio_data,
                mime_type=mime_type
            )
            
            # Generate content with audio understanding
            prompt = self._build_audio_prompt(language_hint, context)
            
            # Use async generation
            response = await asyncio.to_thread(
                self.model.generate_content,
                [audio_part, prompt],
                generation_config={
                    "temperature": 0.3,  # Lower temperature for more accurate transcription
                    "max_output_tokens": 2048,
                    "candidate_count": 1
                }
            )
            
            # Parse response
            result = self._parse_audio_response(response.text)
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            result.processing_time_ms = processing_time_ms
            
            # Estimate audio duration (rough estimate based on file size)
            result.audio_duration_seconds = self._estimate_audio_duration(
                len(audio_data), mime_type
            )
            
            logger.info(
                f"Audio processed successfully: "
                f"length={len(result.transcription)}, "
                f"confidence={result.confidence}, "
                f"language={result.detected_language}, "
                f"time={processing_time_ms}ms"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing audio with Gemini: {e}", exc_info=True)
            # Fallback to basic processing
            return await self._fallback_audio_processing(
                audio_data, mime_type, language_hint
            )
    
    def _build_system_instruction(
        self, 
        language_hint: Optional[str], 
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build system instruction for audio processing"""
        instruction = """You are processing audio input for SafetyBeacon, a disaster support AI assistant.

Your task is to:
1. Accurately transcribe the audio content
2. Detect the language being spoken
3. Identify any emotional tone or urgency
4. Note any background sounds that might indicate the user's environment
5. Extract any disaster-related keywords or concerns

Please provide a structured analysis including:
- Transcription: The exact words spoken
- Language: Detected language code (ja, en, zh, etc.)
- Confidence: Your confidence level (0.0-1.0)
- Emotional tone: calm, anxious, urgent, distressed, etc.
- Background context: Any notable sounds (sirens, alarms, weather, etc.)
- Intent hints: What the user might be asking about"""

        if language_hint:
            instruction += f"\n\nExpected language: {language_hint}"
        
        if context and context.get("location"):
            instruction += f"\n\nUser location: {context['location']}"
        
        return instruction
    
    def _build_audio_prompt(
        self, 
        language_hint: Optional[str], 
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build prompt for audio analysis"""
        prompt = "Please analyze this audio input and provide:"
        prompt += "\n1. Transcription"
        prompt += "\n2. Language detection"
        prompt += "\n3. Emotional tone"
        prompt += "\n4. Background sounds"
        prompt += "\n5. Disaster-related concerns"
        
        if language_hint:
            lang_names = {
                "ja": "Japanese", "en": "English", "zh": "Chinese",
                "ko": "Korean", "es": "Spanish", "fr": "French"
            }
            prompt += f"\n\nNote: The user likely speaks {lang_names.get(language_hint, language_hint)}"
        
        prompt += "\n\nProvide the response in JSON format."
        return prompt
    
    def _parse_audio_response(self, response_text: str) -> AudioProcessingResult:
        """Parse Gemini's audio analysis response"""
        import json
        import re
        
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                # Fallback parsing
                data = self._parse_text_response(response_text)
            
            return AudioProcessingResult(
                transcription=data.get("transcription", ""),
                confidence=float(data.get("confidence", 0.8)),
                detected_language=data.get("language", "ja"),
                emotional_tone=data.get("emotional_tone"),
                background_context=data.get("background_context", {})
            )
            
        except Exception as e:
            logger.error(f"Error parsing audio response: {e}")
            # Return basic result with transcription attempt
            return AudioProcessingResult(
                transcription=self._extract_transcription(response_text),
                confidence=0.5,
                detected_language="ja",
                emotional_tone=None,
                background_context=None
            )
    
    def _parse_text_response(self, text: str) -> Dict[str, Any]:
        """Parse non-JSON text response"""
        result = {
            "transcription": "",
            "language": "ja",
            "confidence": 0.7,
            "emotional_tone": None,
            "background_context": {}
        }
        
        # Simple pattern matching
        patterns = {
            "transcription": r"(?:transcription|text|content)[:：]\s*(.+?)(?:\n|$)",
            "language": r"(?:language|lang)[:：]\s*(\w+)",
            "confidence": r"(?:confidence)[:：]\s*([\d.]+)",
            "emotional_tone": r"(?:emotion|tone)[:：]\s*(\w+)"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if key == "confidence":
                    result[key] = float(value)
                else:
                    result[key] = value
        
        return result
    
    def _extract_transcription(self, text: str) -> str:
        """Extract transcription from unstructured text"""
        # Remove JSON-like structures
        text = re.sub(r'\{.*?\}', '', text, flags=re.DOTALL)
        # Remove common prefixes
        text = re.sub(r'^.*?(?:transcription|said|speaking)[:：]\s*', '', text, flags=re.IGNORECASE)
        # Clean up
        text = text.strip()
        # Take first sentence/paragraph if too long
        if len(text) > 500:
            text = text[:500].rsplit('.', 1)[0] + '.'
        return text
    
    def _estimate_audio_duration(self, file_size: int, mime_type: str) -> float:
        """Estimate audio duration based on file size and format"""
        # Rough estimates based on typical bitrates
        bitrate_estimates = {
            "audio/wav": 1411000,  # 44.1kHz, 16-bit, stereo
            "audio/webm": 128000,  # 128 kbps
            "audio/mp3": 192000,   # 192 kbps
            "audio/mpeg": 192000,
            "audio/ogg": 160000    # 160 kbps
        }
        
        bitrate = bitrate_estimates.get(mime_type, 160000)
        duration = (file_size * 8) / bitrate  # Convert bytes to bits
        return round(duration, 2)
    
    async def _mock_audio_processing(
        self,
        audio_data: bytes,
        mime_type: str,
        language_hint: Optional[str]
    ) -> AudioProcessingResult:
        """Mock audio processing for testing"""
        await asyncio.sleep(0.5)  # Simulate processing time
        
        # Mock responses based on file size (simulate different inputs)
        file_size = len(audio_data)
        
        mock_transcriptions = [
            "地震が発生しました。避難所はどこですか？",
            "津波警報が出ています。高台に避難する必要がありますか？",
            "家族と連絡が取れません。安否確認の方法を教えてください。",
            "緊急地震速報が鳴りました。どうすればいいですか？",
            "近くの病院を教えてください。けが人がいます。"
        ]
        
        # Use file size as seed for consistent mock data
        index = (file_size // 1000) % len(mock_transcriptions)
        
        return AudioProcessingResult(
            transcription=mock_transcriptions[index],
            confidence=0.85 + (index * 0.02),
            detected_language=language_hint or "ja",
            emotional_tone="anxious" if "緊急" in mock_transcriptions[index] else "calm",
            background_context={
                "background_noise": "minimal",
                "audio_quality": "good"
            },
            processing_time_ms=500,
            audio_duration_seconds=float(index + 1)
        )
    
    async def _fallback_audio_processing(
        self,
        audio_data: bytes,
        mime_type: str,
        language_hint: Optional[str]
    ) -> AudioProcessingResult:
        """Fallback processing when Gemini API fails"""
        logger.warning("Using fallback audio processing")
        
        # Basic processing - just return minimal result
        return AudioProcessingResult(
            transcription="[Audio processing temporarily unavailable. Please type your message.]",
            confidence=0.0,
            detected_language=language_hint or "ja",
            emotional_tone=None,
            background_context={"error": "Gemini API unavailable"},
            processing_time_ms=100,
            audio_duration_seconds=0.0
        )
    
    async def analyze_audio_detailed(
        self,
        audio_data: bytes,
        mime_type: str,
        analysis_type: str = "full"
    ) -> AudioAnalysisResult:
        """
        Perform detailed audio analysis for advanced features
        
        Args:
            audio_data: Raw audio bytes
            mime_type: MIME type
            analysis_type: Type of analysis (full, quick, emergency)
            
        Returns:
            Detailed audio analysis result
        """
        # This would be implemented for more advanced audio analysis
        # Including speaker diarization, keyword extraction, etc.
        raise NotImplementedError("Detailed audio analysis not yet implemented")