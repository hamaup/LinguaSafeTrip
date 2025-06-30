from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from .disaster_action_card_schemas import DisasterActionCardSchema

class ChatMessage(BaseModel):
    role: str = Field(..., description="メッセージの送信者 (user/assistant)")
    content: str = Field(..., description="メッセージ内容")

class DisasterChatRequestSchema(BaseModel):
    user_message: str = Field(..., description="ユーザーの最新メッセージ")
    session_id: str = Field(..., description="セッションID")
    current_event_id: str = Field(..., description="現在の災害イベントID")
    chat_history: List[ChatMessage] = Field(
        default_factory=list,
        description="会話履歴 (roleとcontentのリスト)"
    )

class DisasterChatResponseSchema(BaseModel):
    session_id: str
    ai_message: str
    action_cards: Optional[List[DisasterActionCardSchema]] = None
    context_update: Optional[Dict[str, Any]] = None
