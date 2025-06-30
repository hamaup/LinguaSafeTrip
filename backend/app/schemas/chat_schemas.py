# backend/app/schemas/chat_schemas.py
from typing import Tuple, List, Optional
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
from app.schemas.agent import SuggestionCard
from app.schemas.disaster_action_card_schemas import DisasterActionCardSchema
from app.schemas.common.location import Location

# LocationModel は廃止予定 - LocationInfoを使用してください
LocationModel = Location  # Backward compatibility alias

class MessageContext(BaseModel):
    """ PWAが持つ追加コンテキスト情報 (詳細設計書に基づく例) """
    currentLocation: Optional[Location] = Field(None, example={"latitude": 35.68, "longitude": 139.76, "accuracy": 10.5})
    local_contact_count: Optional[int] = Field(None, description="ローカル保存された緊急連絡先の件数")

class ButtonActionType(str, Enum):
    """ ボタンアクションタイプ """
    OPEN_URL = "open_url"
    SEND_SMS = "send_sms"
    SHARE_LOCATION = "share_location"
    CONFIRM_SAFETY = "confirm_safety"
    CALL_NUMBER = "call_number"

class SelectedChoicePayload(BaseModel):
    """ ユーザーが選択したボタンアクションの詳細 """
    action_type: ButtonActionType = Field(..., alias="actionType")
    action_value: Dict[str, Any] = Field(..., alias="actionValue")
    timestamp: datetime = Field(default_factory=datetime.now)

class UserMessage(BaseModel):
    """ ユーザーからのメッセージ内容 """
    text: str = Field(..., description="ユーザーの発話内容")
    language: str = Field(..., description="ユーザーの現在の言語設定 (例: 'ja', 'en')")
    context: Optional[MessageContext] = None
    selected_choice: Optional[SelectedChoicePayload] = Field(None, alias="selectedChoice", description="AI提案への応答やボタン操作など")

class ChatRequest(BaseModel):
    device_id: str = Field(..., min_length=8, max_length=64, pattern=r"^[a-zA-Z0-9-]+$")
    user_input: str = Field(..., min_length=1, max_length=500)
    session_id: Optional[str] = Field(None, min_length=8, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    chat_history: Optional[List[Tuple[str, str]]] = Field(
        None,
        description="Previous conversation turns in [('role', 'message')] format"
    )
    user_language: str = Field("ja", min_length=2, max_length=5)
    is_disaster_mode: bool = False
    user_location: Optional[dict] = Field(
        None,
        examples=[{"latitude": 35.681236, "longitude": 139.767125}]
    )
    local_contact_count: Optional[int] = Field(
        None,
        description="Number of local contacts available"
    )
    external_alerts: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="External emergency alerts from government systems"
    )
    is_voice_input: Optional[bool] = Field(
        False,
        description="Whether input is from voice"
    )
    audio_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Audio processing metadata"
    )
    
    @model_validator(mode='before')
    @classmethod
    def handle_location_alias(cls, data: Any) -> Any:
        """Handle both 'location' and 'user_location' field names"""
        if isinstance(data, dict):
            # If 'location' is present but 'user_location' is not, copy it
            if 'location' in data and 'user_location' not in data:
                data['user_location'] = data['location']
            
            # Handle client_context.emergency_contacts_count
            if 'client_context' in data and isinstance(data['client_context'], dict):
                # Extract emergency_contacts_count from client_context
                if 'emergency_contacts_count' in data['client_context']:
                    data['local_contact_count'] = data['client_context']['emergency_contacts_count']
        return data

class ChatResponse(BaseModel):
    session_id: str = Field(..., alias="sessionId")
    response_text: str = Field(..., alias="responseText")
    updated_chat_history: List[Tuple[str, str]] = Field(..., alias="updatedChatHistory")
    current_task_type: str = Field(..., alias="currentTaskType")
    requires_action: Optional[str] = Field(None, alias="requiresAction")
    action_data: Optional[dict] = Field(None, alias="actionData")
    debug_info: Optional[dict] = Field(None, alias="debugInfo")
    generated_cards_for_frontend: Optional[List[Dict[str, Any]]] = Field(None, alias="generatedCardsForFrontend")
    # 災害モード統合フィールド
    is_emergency_response: Optional[bool] = Field(None, alias="isEmergencyResponse")
    emergency_level: Optional[int] = Field(None, alias="emergencyLevel")
    emergency_actions: Optional[List[str]] = Field(None, alias="emergencyActions")
    action_cards: Optional[List[DisasterActionCardSchema]] = Field(None, alias="actionCards")
