from typing import Dict, List, Any, Optional
from pydantic import BaseModel

class DisasterActionCardButtonSchema(BaseModel):
    label: str
    action_type: str  # "send_message", "request_information", "invoke_tool"
    payload: Dict[str, Any]

class DisasterActionCardSchema(BaseModel):
    card_id: str
    type: str = "disaster_action_card"
    content_markdown: str
    actions: List[DisasterActionCardButtonSchema]
    title: Optional[str] = None
    icon_url: Optional[str] = None
    priority: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class LLMDisasterResponseSchema(BaseModel):
    """LLMからの災害応答スキーマ"""
    response_text: str
    action_cards: List[DisasterActionCardSchema]


class ShelterCard(DisasterActionCardSchema):
    """避難所情報カードのスキーマ"""
    type: str = "shelter_card"
    shelter_name: str
    address: str
    distance_km: Optional[float] = None
    status: Optional[str] = None  # 例: "open", "closed", "full"
    capacity: Optional[int] = None
    facilities: Optional[List[str]] = None
    map_url: Optional[str] = None # Google MapsなどのURL

class ChecklistItemSchema(BaseModel):
    name: str
    description: Optional[str] = None
    checked: bool = False

class ChecklistCard(DisasterActionCardSchema):
    """持ち物リストカードのスキーマ"""
    type: str = "checklist_card"
    items: List[ChecklistItemSchema]
