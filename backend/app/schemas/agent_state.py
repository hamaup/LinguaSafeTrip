"""
Unified agent state definitions.
Consolidates all AgentState variations - this is the authoritative source.
"""

from typing import List, Dict, Any, Optional, Union
from typing_extensions import TypedDict, Annotated
from datetime import datetime
import operator
import logging
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.messages import BaseMessage

from app.schemas.common.location import LocationInfo
from app.schemas.common.enums import TaskType, IntentCategory, EmergencyLevel, LanguageCode
from app.schemas.disaster_info import DisasterContext

logger = logging.getLogger(__name__)

# TypedDict version for LangGraph (required for LangGraph state management)
class AgentState(TypedDict, total=False):
    """
    Agent state for LangGraph workflow.
    This is the authoritative state definition used by the LangGraph workflow engine.
    """
    # User input and conversation - internal processing in English
    user_input: str
    current_user_input: str
    chat_history: List[BaseMessage]
    session_id: str
    device_id: str
    
    # User context
    user_location: Optional[Dict[str, Any]]  # Raw dict for LangGraph compatibility
    user_language: str
    is_disaster_mode: bool
    
    # Intent and routing
    primary_intent: str
    secondary_intents: Annotated[List[str], operator.add]
    intent_confidence: float
    is_disaster_related: bool
    emotional_tone: str
    
    # Processing state
    current_task_type: str
    turn_count: int
    requires_professional_handling: bool
    requires_human_intervention: bool
    conversation_completed: bool
    
    # Responses and actions
    final_response_text: Optional[str]
    off_topic_response: Optional[str]
    generated_cards_for_frontend: List[Dict[str, Any]]
    cards_to_display_queue: List[Dict[str, Any]]
    suggested_actions: Annotated[List[str], operator.add]
    required_action: str
    
    # Context and analysis
    extracted_entities: Dict[str, Any]
    chat_records: Annotated[List[Dict[str, Any]], operator.add]
    recent_alerts: Annotated[List[Dict[str, Any]], operator.add]
    intermediate_results: Dict[str, Any]
    
    # Error handling
    error_message: Optional[str]
    last_askuser_reason: str
    
    # Emergency and urgency
    emergency_level: Optional[str]
    emergency_actions: Optional[List[str]]
    is_emergency_response: bool
    
    # Quality assessment
    quality_retry_count: Optional[int]
    quality_approved: Optional[bool]
    quality_assessment: Optional[Dict[str, Any]]
    quality_rejection_stage: Optional[str]
    quality_rejection_reason: Optional[str]
    
    # Routing
    routing_decision: Optional[Dict[str, str]]
    
    # Language processing
    detected_language: Optional[str]
    
    # Parallel processing support
    parallel_updates: Optional[Dict[str, Any]]
    messages: Optional[List[BaseMessage]]
    
    # SafetyBeacon specific fields
    disaster_context: Optional[DisasterContext]
    current_location: Optional[LocationInfo]
    tool_outputs: Optional[Dict[str, Any]]
    is_awaiting_input: Optional[bool]
    waiting_since: Optional[datetime]
    local_contact_count: Optional[int]

# LocationState for backward compatibility
class LocationState(TypedDict):
    """位置情報の状態モデル"""
    latitude: Optional[float]
    longitude: Optional[float]
    timestamp: Optional[datetime]
    accuracy: Optional[float]

# Pydantic version for API serialization and validation
class AgentStateModel(BaseModel):
    """
    Pydantic version of AgentState for API serialization and validation.
    Used for request/response handling and data validation.
    """
    model_config = ConfigDict(
        extra="allow",  # Allow extra fields for flexibility
        json_schema_extra={
            "example": {
                "user_input": "地震情報を教えて",
                "user_language": "ja",
                "is_disaster_mode": False,
                "primary_intent": "disaster_information",
                "current_task_type": "disaster_info"
            }
        }
    )
    
    # User input and conversation
    user_input: str = Field(..., description="ユーザーの入力")
    current_user_input: Optional[str] = Field(None, description="現在処理中の入力")
    session_id: str = Field(..., description="セッションID")
    device_id: str = Field(..., description="デバイスID")
    
    # User context
    user_location: Optional[LocationInfo] = Field(None, description="ユーザー位置")
    user_language: LanguageCode = Field(default=LanguageCode.JAPANESE, description="ユーザー言語")
    is_disaster_mode: bool = Field(default=False, description="災害モードかどうか")
    
    # Intent and routing
    primary_intent: IntentCategory = Field(default=IntentCategory.UNKNOWN, description="主要意図")
    secondary_intents: List[IntentCategory] = Field(default_factory=list, description="副次意図")
    intent_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="意図の信頼度")
    is_disaster_related: bool = Field(default=False, description="災害関連かどうか")
    emotional_tone: str = Field(default="neutral", description="感情的トーン")
    
    # Processing state
    current_task_type: TaskType = Field(default=TaskType.UNKNOWN, description="現在のタスクタイプ")
    turn_count: int = Field(default=0, ge=0, description="ターン数")
    requires_professional_handling: bool = Field(default=False, description="専門的処理が必要")
    requires_human_intervention: bool = Field(default=False, description="人間の介入が必要")
    conversation_completed: bool = Field(default=False, description="会話が完了")
    
    # Responses and actions
    final_response_text: Optional[str] = Field(None, description="最終応答テキスト")
    off_topic_response: Optional[str] = Field(None, description="オフトピック応答")
    suggested_actions: List[str] = Field(default_factory=list, description="提案アクション")
    required_action: str = Field(default="none", description="必要なアクション")
    
    # Context and analysis
    extracted_entities: Dict[str, Any] = Field(default_factory=dict, description="抽出されたエンティティ")
    intermediate_results: Dict[str, Any] = Field(default_factory=dict, description="中間結果")
    
    # Error handling
    error_message: Optional[str] = Field(None, description="エラーメッセージ")
    last_askuser_reason: str = Field(default="", description="最後の質問理由")
    
    # Emergency and urgency
    emergency_level: Optional[EmergencyLevel] = Field(None, description="緊急レベル")
    emergency_actions: Optional[List[str]] = Field(None, description="緊急時アクション")
    is_emergency_response: bool = Field(default=False, description="緊急応答かどうか")
    
    # Quality assessment
    quality_retry_count: int = Field(default=0, description="品質評価リトライ回数")
    quality_approved: bool = Field(default=False, description="品質承認済み")
    quality_assessment: Optional[Dict[str, Any]] = Field(None, description="品質評価結果")
    quality_rejection_stage: Optional[str] = Field(None, description="品質拒否段階")
    quality_rejection_reason: Optional[str] = Field(None, description="品質拒否理由")
    
    # Language processing
    detected_language: Optional[LanguageCode] = Field(None, description="検出された言語")
    
    def to_langgraph_state(self) -> Dict[str, Any]:
        """Convert to LangGraph-compatible state dict."""
        data = self.model_dump()
        
        # Convert LocationInfo to dict for LangGraph compatibility
        if self.user_location:
            data['user_location'] = self.user_location.model_dump()
        
        # Convert enums to strings
        data['user_language'] = self.user_language.value
        data['primary_intent'] = self.primary_intent.value
        data['secondary_intents'] = [intent.value for intent in self.secondary_intents]
        data['current_task_type'] = self.current_task_type.value
        
        if self.emergency_level:
            data['emergency_level'] = self.emergency_level.value
        if self.detected_language:
            data['detected_language'] = self.detected_language.value
            
        return data
    
    @classmethod
    def from_langgraph_state(cls, state: Dict[str, Any]) -> "AgentStateModel":
        """Create from LangGraph state dict."""
        # Convert location dict to LocationInfo
        if state.get('user_location') and isinstance(state['user_location'], dict):
            state['user_location'] = LocationInfo(**state['user_location'])
        
        # Handle enum conversions safely with proper fallbacks
        enum_conversions = [
            ('user_language', LanguageCode, LanguageCode.JAPANESE),
            ('primary_intent', IntentCategory, IntentCategory.UNKNOWN),
            ('current_task_type', TaskType, TaskType.UNKNOWN),
            ('emergency_level', EmergencyLevel, None),  # Optional field
            ('detected_language', LanguageCode, None)   # Optional field
        ]
        
        for field_name, enum_class, default_value in enum_conversions:
            if field_name in state and isinstance(state[field_name], str):
                try:
                    state[field_name] = enum_class(state[field_name])
                except ValueError as e:
                    logger.warning(f"Invalid enum value for {field_name}: {state[field_name]}. Using default: {default_value}")
                    if default_value is not None:
                        state[field_name] = default_value
                    else:
                        # Remove invalid optional field
                        state.pop(field_name, None)
        
        # Convert secondary_intents with error handling
        if 'secondary_intents' in state and isinstance(state['secondary_intents'], list):
            converted_intents = []
            for intent in state['secondary_intents']:
                if isinstance(intent, str):
                    try:
                        converted_intents.append(IntentCategory(intent))
                    except ValueError:
                        logger.warning(f"Invalid secondary intent: {intent}. Skipping.")
                        continue
                else:
                    converted_intents.append(intent)
            state['secondary_intents'] = converted_intents
        
        return cls(**{k: v for k, v in state.items() if k in cls.model_fields})

# Type aliases for convenience
AgentStateDict = Dict[str, Any]
