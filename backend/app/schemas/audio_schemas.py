"""
Audio-related schemas for voice chat functionality
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime

class AudioChatRequest(BaseModel):
    """音声チャットリクエストのスキーマ"""
    audio_data: bytes = Field(..., description="Audio file binary data")
    mime_type: str = Field("audio/wav", description="MIME type of audio file")
    device_id: str = Field(..., description="Device identifier")
    session_id: str = Field(..., description="Chat session ID")
    user_location: Optional[Dict[str, float]] = Field(None, description="User location (lat, lon)")
    language_code: Optional[str] = Field("ja", description="Expected language code")
    
    @validator('mime_type')
    def validate_mime_type(cls, v):
        allowed_types = ["audio/wav", "audio/webm", "audio/mp3", "audio/mpeg", "audio/ogg"]
        if v not in allowed_types:
            raise ValueError(f"Unsupported audio format. Allowed: {allowed_types}")
        return v
    
    class Config:
        json_encoders = {
            bytes: lambda v: v.decode('utf-8') if v else None
        }

class AudioProcessingResult(BaseModel):
    """音声処理結果のスキーマ"""
    transcription: str = Field(..., description="Transcribed text from audio")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Transcription confidence score")
    detected_language: str = Field(..., description="Detected language code")
    emotional_tone: Optional[str] = Field(None, description="Detected emotional tone")
    background_context: Optional[Dict[str, Any]] = Field(None, description="Background noise/context info")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    audio_duration_seconds: Optional[float] = Field(None, description="Duration of audio in seconds")
    
class AudioMetadata(BaseModel):
    """音声メタデータのスキーマ"""
    format: str = Field(..., description="Audio format (wav, webm, etc)")
    sample_rate: Optional[int] = Field(None, description="Sample rate in Hz")
    channels: Optional[int] = Field(None, description="Number of audio channels")
    bit_depth: Optional[int] = Field(None, description="Bit depth")
    duration_seconds: float = Field(..., description="Duration in seconds")
    file_size_bytes: int = Field(..., description="File size in bytes")

class AudioAnalysisResult(BaseModel):
    """詳細な音声分析結果"""
    transcription: str
    confidence: float
    language: str
    segments: Optional[List[Dict[str, Any]]] = Field(None, description="Time-aligned segments")
    speaker_count: Optional[int] = Field(None, description="Number of detected speakers")
    keywords: Optional[List[str]] = Field(None, description="Extracted keywords")
    summary: Optional[str] = Field(None, description="Brief summary of content")
    intent_hints: Optional[List[str]] = Field(None, description="Detected intent hints")
    
class AudioErrorResponse(BaseModel):
    """音声処理エラーレスポンス"""
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AudioLimits(BaseModel):
    """音声処理の制限事項"""
    max_file_size_mb: int = Field(10, description="Maximum file size in MB")
    max_duration_seconds: int = Field(60, description="Maximum audio duration in seconds")
    supported_formats: List[str] = Field(
        default=["wav", "webm", "mp3", "mpeg", "ogg"],
        description="Supported audio formats"
    )
    min_sample_rate_hz: int = Field(8000, description="Minimum sample rate")
    max_sample_rate_hz: int = Field(48000, description="Maximum sample rate")