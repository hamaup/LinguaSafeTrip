"""
Agent routing and intent classification schemas.
Consolidates routing decision and intent classification logic.
"""

from typing import Literal, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from ..common.enums import IntentCategory, TaskType

class RoutingDecision(BaseModel):
    """
    Routing decision for conversation flow.
    """
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        json_schema_extra={
            "example": {
                "next_node": "disaster_info_node",
                "reason": "ユーザーが災害情報を要求",
                "confidence": 0.9
            }
        }
    )

    next_node: Literal[
        "improved_off_topic_handler",
        "disaster_info_node", 
        "evacuation_support_node",
        "information_guide_node",
        "emergency_response_node",
        "safety_confirmation_node",
        "communication_node",
        "response_generator",
        "router_node",
        "disaster_context_manager",
        "END"
    ] = Field(description="次に実行すべきノード名")
    
    reason: str = Field(description="ノード選択理由", max_length=200)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="ルーティング判定の信頼度")
    
    # Additional context
    alternative_nodes: Optional[Dict[str, float]] = Field(
        None,
        description="代替ノードとそのスコア"
    )
    processing_notes: Optional[str] = Field(
        None,
        max_length=500,
        description="処理に関する追加メモ"
    )

class DisasterIntentSchema(BaseModel):
    """
    Disaster-related intent classification result.
    Enhanced from routing_schemas.py
    """
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "is_disaster_related": True,
                "primary_intent": "disaster_information", 
                "confidence": 0.9,
                "reasoning": "地震情報を問い合わせている",
                "urgency_level": 2
            }
        }
    )
    
    is_disaster_related: bool = Field(description="災害に関連する内容かどうか")
    primary_intent: IntentCategory = Field(description="主要な意図カテゴリ")
    confidence: float = Field(description="分類の信頼度", ge=0.0, le=1.0)
    reasoning: str = Field(description="分類の根拠", max_length=500)
    
    # Enhanced fields
    urgency_level: int = Field(default=0, ge=0, le=5, description="緊急度レベル (0-5)")
    secondary_intents: list[IntentCategory] = Field(
        default_factory=list,
        description="副次的な意図"
    )
    
    # Context analysis
    emotional_indicators: Optional[Dict[str, float]] = Field(
        None,
        description="感情指標 (fear, urgency, confusion, etc.)"
    )
    
    location_mentioned: bool = Field(default=False, description="位置情報が言及されているか")
    time_sensitive: bool = Field(default=False, description="時間に敏感な内容か")
    
    # Suggested routing
    suggested_task_type: TaskType = Field(
        default=TaskType.UNKNOWN,
        description="推奨タスクタイプ"
    )
    
    requires_immediate_action: bool = Field(
        default=False,
        description="即座の対応が必要か"
    )

class IntentClassificationRequest(BaseModel):
    """
    Request for intent classification.
    """
    model_config = ConfigDict(extra="forbid")
    
    user_input: str = Field(..., min_length=1, max_length=1000, description="ユーザー入力")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="コンテキスト情報")
    
    # Optional previous context
    previous_intent: Optional[IntentCategory] = Field(None, description="前回の意図")
    conversation_history: Optional[list[str]] = Field(None, description="会話履歴（簡略版）")
    
    # User state
    is_disaster_mode: bool = Field(default=False, description="災害モードかどうか")
    user_location_available: bool = Field(default=False, description="位置情報が利用可能か")
    
    # Processing options
    include_emotional_analysis: bool = Field(default=False, description="感情分析を含めるか")
    include_urgency_detection: bool = Field(default=True, description="緊急度検出を含めるか")

class RouteAnalysis(BaseModel):
    """
    Comprehensive routing analysis result.
    """
    model_config = ConfigDict(extra="forbid")
    
    # Intent classification
    intent_result: DisasterIntentSchema = Field(..., description="意図分類結果")
    
    # Routing decision
    routing_decision: RoutingDecision = Field(..., description="ルーティング決定")
    
    # Analysis metadata
    processing_time_ms: float = Field(..., ge=0, description="処理時間")
    model_version: str = Field(..., description="使用モデルバージョン")
    
    # Quality indicators
    classification_quality: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="分類品質スコア"
    )
    
    # Debug information
    debug_info: Optional[Dict[str, Any]] = Field(
        None,
        description="デバッグ情報"
    )