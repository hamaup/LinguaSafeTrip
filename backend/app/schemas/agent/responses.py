"""
Agent response schemas.
Consolidates all response-related data structures.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from ..common.enums import TaskType, EmergencyLevel, LanguageCode

class AgentResponse(BaseModel):
    """
    Unified agent response model.
    Consolidates response structures from various modules.
    """
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "response_text": "こんにちは！防災アシスタントのLinguaSafeTripです。",
                "current_task_type": "greeting",
                "status": "success"
            }
        }
    )
    
    # Core response
    response_text: str = Field(..., description="応答テキスト")
    current_task_type: TaskType = Field(default=TaskType.UNKNOWN, description="処理タスクタイプ")
    status: str = Field(default="success", description="処理状態")
    
    # Additional content
    mentioned_cards: List[str] = Field(default_factory=list, description="言及されたカードID")
    generated_cards_for_frontend: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="フロントエンド用生成カード（シリアライズ済み）"
    )
    
    # Actions and requirements
    requires_action: Optional[str] = Field(
        None,
        description="必要なアクション種別"
    )
    action_data: Optional[Dict[str, Any]] = Field(
        None,
        description="アクションデータ"
    )
    suggested_actions: List[str] = Field(
        default_factory=list,
        description="提案アクション"
    )
    
    # Emergency response fields
    is_emergency_response: bool = Field(default=False, description="緊急応答かどうか")
    emergency_level: Optional[EmergencyLevel] = Field(None, description="緊急レベル")
    emergency_actions: Optional[List[str]] = Field(None, description="緊急時アクション")
    
    # Error handling
    error_details: Optional[Dict[str, Any]] = Field(None, description="エラー詳細")
    
    # Debug and metadata
    debug_info: Dict[str, Any] = Field(default_factory=dict, description="デバッグ情報")
    processing_time_ms: Optional[float] = Field(None, ge=0, description="処理時間（ミリ秒）")
    
    # Language and localization
    response_language: Optional[LanguageCode] = Field(None, description="応答言語")
    
    # Session management
    session_id: Optional[str] = Field(None, description="セッションID")
    turn_count: Optional[int] = Field(None, ge=0, description="ターン数")
    conversation_completed: bool = Field(default=False, description="会話完了フラグ")
    chat_history: Optional[List[Any]] = Field(None, description="チャット履歴（LangGraph統合）")

class ErrorResponse(BaseModel):
    """
    Error response model for failed requests.
    """
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "error_type": "validation_error",
                "message": "Invalid input format",
                "status": "error"
            }
        }
    )
    
    error_type: str = Field(..., description="エラータイプ")
    message: str = Field(..., description="エラーメッセージ")
    status: str = Field(default="error", description="ステータス")
    
    # Error details
    details: Optional[Dict[str, Any]] = Field(None, description="詳細情報")
    error_code: Optional[str] = Field(None, description="エラーコード")
    
    # Context
    request_id: Optional[str] = Field(None, description="リクエストID")
    timestamp: Optional[str] = Field(None, description="エラー発生時刻")
    
    # Suggestions for recovery
    suggested_actions: List[str] = Field(
        default_factory=list,
        description="推奨される対処法"
    )
    retry_possible: bool = Field(default=True, description="リトライ可能かどうか")

class StreamingResponse(BaseModel):
    """
    Streaming response for real-time updates.
    """
    model_config = ConfigDict(extra="forbid")
    
    chunk_id: str = Field(..., description="チャンクID")
    chunk_type: str = Field(..., description="チャンクタイプ")
    content: str = Field(..., description="チャンク内容")
    
    # Streaming control
    is_complete: bool = Field(default=False, description="ストリーム完了フラグ")
    sequence_number: int = Field(default=0, ge=0, description="シーケンス番号")
    
    # Context
    session_id: str = Field(..., description="セッションID")
    total_chunks: Optional[int] = Field(None, ge=1, description="総チャンク数")

class ResponseMetrics(BaseModel):
    """
    Response performance metrics.
    """
    model_config = ConfigDict(extra="forbid")
    
    # Timing metrics
    total_time_ms: float = Field(..., ge=0, description="総処理時間")
    llm_time_ms: Optional[float] = Field(None, ge=0, description="LLM処理時間")
    tool_time_ms: Optional[float] = Field(None, ge=0, description="ツール実行時間")
    
    # Quality metrics
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="信頼度スコア")
    relevance_score: Optional[float] = Field(None, ge=0, le=1, description="関連性スコア")
    
    # Usage metrics
    input_tokens: Optional[int] = Field(None, ge=0, description="入力トークン数")
    output_tokens: Optional[int] = Field(None, ge=0, description="出力トークン数")
    
    # Context
    model_used: Optional[str] = Field(None, description="使用モデル")
    tools_used: List[str] = Field(default_factory=list, description="使用ツール")