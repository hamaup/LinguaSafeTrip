# backend/app/schemas/heartbeat.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum

from app.schemas.common.location import Location
from app.schemas.device import NetworkType


class DeviceMode(str, Enum):
    """デバイスモード"""
    NORMAL = "normal"
    EMERGENCY = "emergency"


class UserActionType(str, Enum):
    """ユーザーアクションの種類"""
    ACKNOWLEDGED = "acknowledged"  # 提案を確認した
    DISMISSED = "dismissed"       # 提案を却下した
    COMPLETED = "completed"       # 提案のアクションを実行した
    FAVORITED = "favorited"       # 提案をお気に入りにした
    SHARED = "shared"            # 提案を共有した
    FEEDBACK = "feedback"        # フィードバックを送信した


class HeartbeatDeviceStatus(BaseModel):
    """ハートビート用デバイス状態"""
    location: Optional[Dict[str, float]] = Field(None, description="GPS location (latitude, longitude)")
    battery_level: Optional[int] = Field(None, ge=0, le=100, description="Battery level percentage")
    is_charging: Optional[bool] = Field(None, description="Whether device is charging")
    network_type: Optional[NetworkType] = Field(None, description="Network connection type")
    signal_strength: Optional[int] = Field(None, ge=0, le=5, description="Signal strength (0-5)")


class ClientContext(BaseModel):
    """クライアントコンテキスト"""
    current_mode: DeviceMode = Field(DeviceMode.NORMAL, description="Current client mode")
    language_code: str = Field("ja", description="Language code")
    last_sync_timestamp: Optional[datetime] = Field(None, description="Last sync timestamp")
    acknowledged_suggestion_types: List[str] = Field(default_factory=list, description="Recently acknowledged suggestion types")
    recent_actions: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Recent user actions on suggestions")
    reset_suggestion_history: bool = Field(False, description="Reset suggestion history flag for app restart/initialization")
    emergency_contacts_count: int = Field(0, description="Number of emergency contacts registered")
    permissions: Optional[Dict[str, bool]] = Field(None, description="Client permission status")


class UserActionRequest(BaseModel):
    """ユーザーアクション記録リクエスト"""
    device_id: str = Field(..., description="Device ID")
    action_type: UserActionType = Field(..., description="Action type")
    suggestion_type: Optional[str] = Field(None, description="Suggestion type that was acted upon")
    action_data: Optional[Dict[str, Any]] = Field(None, description="Additional action data")
    session_id: Optional[str] = Field(None, description="Current session ID")
    user_feedback: Optional[str] = Field(None, description="User feedback text")


class HeartbeatRequest(BaseModel):
    """ハートビートリクエスト"""
    device_id: str = Field(..., description="Device ID")
    device_status: Optional[HeartbeatDeviceStatus] = Field(None, description="Device status")
    client_context: ClientContext = Field(..., description="Client context")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "device_id": "device_123",
                "device_status": {
                    "location": {
                        "latitude": 35.6812,
                        "longitude": 139.7671,
                        "accuracy": 10.5
                    },
                    "battery_level": 75,
                    "is_charging": False,
                    "network_type": "wifi",
                    "signal_strength": 4
                },
                "client_context": {
                    "current_mode": "normal",
                    "language_code": "ja",
                    "last_sync_timestamp": "2024-01-20T10:00:00Z",
                    "acknowledged_suggestion_types": ["guide_recommendation", "disaster_info"],
                    "reset_suggestion_history": False
                }
            }
        }
    }


class DisasterAlert(BaseModel):
    """災害アラート情報"""
    alert_id: str = Field(..., description="Alert ID")
    type: str = Field(..., description="Alert type")
    severity: str = Field(..., description="Severity level")
    title: str = Field(..., description="Alert title")
    issued_at: datetime = Field(..., description="Issue timestamp")


class NearestShelter(BaseModel):
    """最寄り避難所情報"""
    shelter_id: str = Field(..., description="Shelter ID")
    name: str = Field(..., description="Shelter name")
    distance_km: float = Field(..., description="Distance in km")
    status: str = Field(..., description="Shelter status")


class DisasterStatus(BaseModel):
    """災害ステータス"""
    mode: DeviceMode = Field(..., description="Server-determined mode")
    mode_reason: Optional[str] = Field(None, description="Reason for mode")
    active_alerts: List[DisasterAlert] = Field(default_factory=list, description="Active disaster alerts")
    nearest_shelter: Optional[NearestShelter] = Field(None, description="Nearest shelter info")


class ProactiveSuggestion(BaseModel):
    """プロアクティブ提案"""
    type: str = Field(..., description="Suggestion type")
    content: str = Field(..., description="Suggestion content")
    priority: str = Field(..., description="Priority level")
    action_query: Optional[str] = Field(None, description="Action query for chat")
    action_display_text: Optional[str] = Field(None, description="Display text for action button")
    action_data: Optional[Dict[str, Any]] = Field(None, description="Additional action data for processing")
    expires_at: Optional[datetime] = Field(None, description="Expiration time")


class SyncConfig(BaseModel):
    """同期設定"""
    min_sync_interval: int = Field(30, description="Minimum sync interval")
    force_refresh: bool = Field(False, description="Force refresh flag")


class HeartbeatResponse(BaseModel):
    """ハートビートレスポンス"""
    sync_id: str = Field(..., description="Sync ID")
    server_timestamp: datetime = Field(..., description="Server timestamp")
    disaster_status: DisasterStatus = Field(..., description="Disaster status")
    proactive_suggestions: List[ProactiveSuggestion] = Field(default_factory=list, description="Proactive suggestions")
    sync_config: SyncConfig = Field(..., description="Sync configuration")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "sync_id": "sync_20240120_100500_123",
                "server_timestamp": "2024-01-20T10:05:00Z",
                "disaster_status": {
                    "mode": "emergency",
                    "mode_reason": "震度5強の地震が発生しています",
                    "active_alerts": [
                        {
                            "alert_id": "eq_2024_001",
                            "type": "earthquake",
                            "severity": "warning",
                            "title": "緊急地震速報",
                            "issued_at": "2024-01-20T10:00:00Z"
                        }
                    ],
                    "nearest_shelter": {
                        "shelter_id": "shelter_001",
                        "name": "○○小学校",
                        "distance_km": 0.8,
                        "status": "開設済"
                    }
                },
                "proactive_suggestions": [
                    {
                        "type": "emergency_action",
                        "content": "強い揺れに警戒してください",
                        "priority": "critical",
                        "action_query": "地震の対処法を教えて"
                    }
                ],
                "sync_config": {
                    "min_sync_interval": 30,
                    "force_refresh": False
                }
            }
        }
    }


class HeartbeatError(BaseModel):
    """ハートビートエラー"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    retry_after: Optional[int] = Field(None, description="Retry after seconds")


class UserActionRequest(BaseModel):
    """ユーザーアクション記録リクエスト"""
    device_id: str = Field(..., description="Device ID")
    action_type: UserActionType = Field(..., description="Action type")
    suggestion_type: Optional[str] = Field(None, description="Related suggestion type")
    action_data: Optional[Dict[str, Any]] = Field(None, description="Additional action data")
    session_id: Optional[str] = Field(None, description="Session ID")
    user_feedback: Optional[str] = Field(None, description="User feedback text")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "device_id": "device_123",
                "action_type": "acknowledged",
                "suggestion_type": "emergency_alert",
                "action_data": {
                    "suggestion_id": "sugg_456",
                    "execution_time_ms": 1200
                },
                "session_id": "session_789",
                "user_feedback": "Very helpful suggestion"
            }
        }
    }