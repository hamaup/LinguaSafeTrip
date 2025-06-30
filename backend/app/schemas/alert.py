from enum import Enum
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.schemas.common.enums import EmergencyLevel

class AlertLevel(Enum):
    """アラートレベル定義（数値ベース - 互換性のため保持）"""
    NORMAL = 0       # 情報なし／平常
    CAUTION = 1      # 注意レベル
    WARNING = 2      # 警戒レベル
    DANGER = 3       # 危険レベル
    EMERGENCY = 4    # 非常に危険／特別警報レベル
    
    @classmethod
    def from_emergency_level(cls, level: EmergencyLevel) -> 'AlertLevel':
        """EmergencyLevelからAlertLevelへの変換"""
        mapping = {
            EmergencyLevel.NORMAL: cls.NORMAL,
            EmergencyLevel.ADVISORY: cls.CAUTION,
            EmergencyLevel.WARNING: cls.WARNING,
            EmergencyLevel.CRITICAL: cls.DANGER,
            EmergencyLevel.EMERGENCY: cls.EMERGENCY
        }
        return mapping.get(level, cls.NORMAL)


class LatestAlertSummary(BaseModel):
    """最新アラートの概要情報"""
    alert_id: str = Field(..., description="アラートの一意なID")
    alert_type: str = Field(..., description="アラートの種類（地震、津波など）")
    level: AlertLevel = Field(..., description="アラートレベル")
    title: str = Field(..., description="アラートのタイトル")
    summary: str = Field(..., description="アラートの概要")
    received_at: datetime = Field(..., description="アラート受信日時")
    affected_areas: List[str] = Field(default_factory=list,
                                   description="影響を受ける地域コードリスト")
    source: str = Field(..., description="アラート情報源（気象庁など）")
    is_active: bool = Field(True, description="アラートが有効かどうか")

    @field_validator('alert_id')
    def validate_alert_id(cls, v: str) -> str:
        """アラートIDのバリデーション"""
        if not v or len(v) < 5:
            raise ValueError('Alert ID must be at least 5 characters long')
        return v

    @field_validator('alert_type')
    def validate_alert_type(cls, v: str) -> str:
        """アラートタイプのバリデーション"""
        valid_types = ['earthquake', 'tsunami', 'weather', 'volcano', 'other']
        if v not in valid_types:
            raise ValueError(f'Invalid alert type. Must be one of: {valid_types}')
        return v

class AlertHistoryCreate(BaseModel):
    """アラート履歴作成用スキーマ"""
    alert_id: str = Field(..., min_length=5, max_length=50)
    alert_type: str = Field(..., pattern=r'^(earthquake|tsunami|weather|volcano|other)$')
    level: AlertLevel
    title: str = Field(..., max_length=100)
    summary: str = Field(..., max_length=500)
    received_at: datetime
    affected_areas: List[str] = Field(default_factory=list)
    source: str = Field(..., max_length=50)
    is_active: bool = Field(default=True)
    user_id: Optional[str] = Field(None, max_length=50)
    device_id: Optional[str] = Field(None, max_length=50)

    model_config = ConfigDict(from_attributes=True)

class FcmAlertInfo(BaseModel):
    """FCM通知用アラート情報"""
    id: str = Field(..., min_length=5, max_length=50)
    type: str = Field(..., pattern=r'^(earthquake|tsunami|weather|volcano|other)$')
    level: AlertLevel
    title: str = Field(..., max_length=100)
    body: str = Field(..., max_length=500)
    timestamp: datetime
    areas: List[str] = Field(default_factory=list)
    user_id: str = Field(..., max_length=50)
    device_token: Optional[str] = Field(None, max_length=200)
    deep_link: Optional[str] = Field(None, max_length=200)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "alert_12345",
            "type": "earthquake",
            "level": "WARNING",
            "title": "地震警報",
            "body": "震度5弱の地震が発生しました",
            "timestamp": "2025-05-26T12:00:00+09:00",
            "areas": ["東京都", "神奈川県"],
            "user_id": "user_123",
            "device_token": "fcm_token_abc123",
            "deep_link": "safetybeacon://alerts/alert_12345"
        }
    })
