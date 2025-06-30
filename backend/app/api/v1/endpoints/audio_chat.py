"""
Audio chat endpoint for voice-based interactions using Gemini Audio Understanding API
"""
import os
import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
# from sqlalchemy.orm import Session  # Not needed for now

# Remove unused dependency imports for now
from app.schemas.audio_schemas import (
    AudioChatRequest, 
    AudioProcessingResult,
    AudioErrorResponse,
    AudioLimits
)
from app.schemas.chat_schemas import ChatRequest, ChatResponse
from app.services.audio_processing_service import AudioProcessingService
from app.agents.safety_beacon_agent.core.main_orchestrator import run_agent_interaction
# from app.utils.performance import measure_execution_time  # Not needed for now

logger = logging.getLogger(__name__)

router = APIRouter()

# Audio processing limits
AUDIO_LIMITS = AudioLimits()

@router.post("/audio", response_model=ChatResponse)
async def process_audio_chat(
    audio_file: UploadFile = File(...),
    device_id: str = Form(...),
    session_id: str = Form(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    language_code: Optional[str] = Form("ja"),
    # db: Session = Depends(get_db)  # Not needed for audio processing
) -> ChatResponse:
    """
    Process audio input for chat using Gemini Audio Understanding API
    
    Args:
        audio_file: Audio file upload (WAV, WebM, MP3, etc.)
        device_id: Device identifier
        session_id: Chat session ID
        latitude: Optional user latitude
        longitude: Optional user longitude
        language_code: Expected language code
        db: Database session
    
    Returns:
        ChatResponse with processed result
    """
    try:
        # Validate file size
        audio_data = await audio_file.read()
        file_size_mb = len(audio_data) / (1024 * 1024)
        
        if file_size_mb > AUDIO_LIMITS.max_file_size_mb:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Audio file too large. Maximum size: {AUDIO_LIMITS.max_file_size_mb}MB"
            )
        
        # Validate file format
        content_type = audio_file.content_type or "audio/wav"
        if not any(fmt in content_type for fmt in AUDIO_LIMITS.supported_formats):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported audio format. Supported: {AUDIO_LIMITS.supported_formats}"
            )
        
        logger.info(
            f"Processing audio chat: device={device_id}, session={session_id}, "
            f"size={file_size_mb:.2f}MB, format={content_type}"
        )
        
        # Initialize audio processing service
        audio_service = AudioProcessingService()
        
        # Process audio with Gemini Audio Understanding
        processing_result = await audio_service.process_audio_input(
            audio_data=audio_data,
            mime_type=content_type,
            language_hint=language_code,
            context={
                "device_id": device_id,
                "session_id": session_id,
                "location": {"latitude": latitude, "longitude": longitude} if latitude and longitude else None
            }
        )
        
        # Log processing results
        logger.info(
            f"Audio processed successfully: "
            f"transcription_length={len(processing_result.transcription)}, "
            f"confidence={processing_result.confidence:.2f}, "
            f"language={processing_result.detected_language}"
        )
        
        # Create chat request from transcribed audio
        user_location = None
        if latitude is not None and longitude is not None:
            user_location = {
                "latitude": latitude,
                "longitude": longitude,
                "accuracy": 0,  # Unknown from audio request
                "timestamp": datetime.utcnow().isoformat()
            }
        
        chat_request = ChatRequest(
            user_input=processing_result.transcription,
            device_id=device_id,
            session_id=session_id,
            user_location=user_location,
            is_voice_input=True,  # Mark as voice input
            audio_metadata={
                "confidence": processing_result.confidence,
                "detected_language": processing_result.detected_language,
                "emotional_tone": processing_result.emotional_tone,
                "processing_time_ms": processing_result.processing_time_ms,
                "duration_seconds": processing_result.audio_duration_seconds
            }
        )
        
        # Process through existing chat pipeline
        response = await run_agent_interaction(chat_request)
        
        # Add audio-specific metadata to response
        if hasattr(response, 'metadata') and response.metadata:
            response.metadata['audio_processing'] = {
                "transcription_confidence": processing_result.confidence,
                "detected_language": processing_result.detected_language,
                "emotional_tone": processing_result.emotional_tone,
                "background_context": processing_result.background_context
            }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing audio chat: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process audio: {str(e)}"
        )

@router.get("/audio/limits", response_model=AudioLimits)
async def get_audio_limits() -> AudioLimits:
    """Get audio processing limits and supported formats"""
    return AUDIO_LIMITS

@router.post("/audio/validate")
async def validate_audio_file(
    audio_file: UploadFile = File(...),
) -> Dict[str, Any]:
    """
    Validate audio file without processing
    
    Returns metadata about the audio file
    """
    try:
        audio_data = await audio_file.read()
        file_size_mb = len(audio_data) / (1024 * 1024)
        
        # Basic validation
        is_valid = True
        errors = []
        
        if file_size_mb > AUDIO_LIMITS.max_file_size_mb:
            is_valid = False
            errors.append(f"File too large: {file_size_mb:.2f}MB > {AUDIO_LIMITS.max_file_size_mb}MB")
        
        content_type = audio_file.content_type or "unknown"
        if not any(fmt in content_type for fmt in AUDIO_LIMITS.supported_formats):
            is_valid = False
            errors.append(f"Unsupported format: {content_type}")
        
        return {
            "is_valid": is_valid,
            "file_name": audio_file.filename,
            "content_type": content_type,
            "file_size_mb": round(file_size_mb, 2),
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error validating audio file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to validate audio file: {str(e)}"
        )