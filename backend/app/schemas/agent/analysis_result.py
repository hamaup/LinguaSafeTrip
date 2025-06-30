from pydantic import BaseModel, ConfigDict, Field
from typing import Dict, List, Any, Optional

class AnalysisResult(BaseModel):
    """LLM分析結果のスキーマ定義"""
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        json_schema_extra={
            "example": {
                "is_disaster_related": True,
                "primary_intent": "evacuation_request",
                "required_action": "provide_shelter_info",
                "reasoning": "ユーザーが避難情報を要求",
                "secondary_intents": ["information_request"],
                "extracted_entities": {"location": "東京"},
                "emotional_tone": "urgent",
                "disaster_relevance": 0.8
            }
        }
    )

    is_disaster_related: bool = Field(default=False)
    primary_intent: str = Field(default="unknown", pattern=r"^[a-z_]+$")  # スネークケース強制
    required_action: str = Field(default="respond_general")
    reasoning: str = Field(default="Fallback processing")
    secondary_intents: List[str] = Field(default_factory=list)
    extracted_entities: Dict[str, Any] = Field(default_factory=dict)
    emotional_tone: str = Field(default="neutral", pattern=r"^[a-z]+$")
    disaster_relevance: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    def to_state_updates(self) -> Dict[str, Any]:
        """AgentStateにマッピングするための変換メソッド"""
        return {
            "primary_intent": self.primary_intent,
            "required_action": self.required_action,
            "emotional_tone": self.emotional_tone,
            "extracted_entities": self.extracted_entities,
            "secondary_intents": self.secondary_intents,
            "disaster_relevance": self.disaster_relevance or 0.0
        }
