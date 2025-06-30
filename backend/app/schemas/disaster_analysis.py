from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Literal, Optional

class DisasterAnalysisResult(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    is_disaster_related: bool = Field(False, description="災害関連か否か")
    primary_intent: str = Field("unknown", description="一次意図")
    secondary_intents: List[str] = Field(default_factory=list, description="二次意図のリスト")
    extracted_entities: Dict[str, List[str]] = Field(default_factory=dict, description="抽出エンティティ")
    required_action: Literal["none", "monitor", "prepare", "evacuation", "alert", "evacuate", "retry_with_fixed_input", "template_error", "error_handled"] = Field("none", description="必要なアクション")
    reasoning: Optional[str] = Field(None, description="推論やエラー理由")
    emotional_tone: str = Field("neutral", description="ユーザーの感情トーン")
    
    # LLMからの追加フィールドを許可
    intent_category: Optional[str] = Field(None, description="意図カテゴリ")
    confidence: Optional[float] = Field(None, description="信頼度")
    user_situation: Optional[str] = Field(None, description="ユーザーの状況")
    response_type: Optional[str] = Field(None, description="応答タイプ")
    recommended_action: Optional[str] = Field(None, description="推奨アクション")
    search_keywords: Optional[List[str]] = Field(None, description="検索キーワード")
    needs_location: Optional[bool] = Field(None, description="位置情報が必要か")


class DisasterIntentSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    is_disaster_related: bool = Field(..., description="災害関連かどうか")
    primary_intent: str = Field(..., description="主要意図")
    confidence: float = Field(..., description="判定の確信度", ge=0, le=1)
    reasoning: Optional[str] = Field(None, description="判定理由")


class DisasterDetailedIntentResult(BaseModel):
    """災害関連質問の詳細分類結果"""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    
    intent_category: Literal[
        "shelter_search",
        "earthquake_guidance", 
        "earthquake_info",
        "disaster_preparation",
        "emergency_contact",
        "safety_confirmation",
        "evacuation_guidance",
        "disaster_news",
        "general_disaster",
        "other"
    ] = Field(..., description="詳細分類カテゴリ")
    
    confidence: float = Field(..., ge=0.0, le=1.0, description="信頼度")
    reasoning: str = Field(..., description="分類理由")
    needs_location: bool = Field(..., description="位置情報が必要かどうか")
    urgency_level: int = Field(..., ge=1, le=5, description="緊急度レベル")
