# backend/app/schemas/disaster_intent.py
from typing import Literal, Optional
from pydantic import BaseModel, Field

class DisasterIntentClassification(BaseModel):
    """災害関連質問の詳細分類結果"""
    intent_category: Literal[
        "shelter_search",
        "earthquake_guidance", 
        "earthquake_info",
        "disaster_preparation",
        "emergency_contact",
        "safety_confirmation",
        "general_disaster",
        "other"
    ] = Field(..., description="分類カテゴリ")
    
    confidence: float = Field(..., ge=0.0, le=1.0, description="信頼度")
    reasoning: str = Field(..., description="分類理由")
    needs_location: bool = Field(..., description="位置情報が必要かどうか")
    urgency_level: int = Field(..., ge=1, le=5, description="緊急度レベル")