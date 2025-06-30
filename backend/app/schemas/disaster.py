from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class JMAEvent(BaseModel):
    """気象庁の災害イベントデータモデル"""
    id: str
    title: str
    latitude: float
    longitude: float
    occurred_at: datetime
    event_type: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None

class RelevantDisasterEvent(BaseModel):
    """関連災害イベントデータモデル"""
    source: str = "JMA"
    title: str
    location: str
    occurred_at: datetime
    distance_km: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    details: Optional[dict] = None

# 新しい災害監視関連スキーマ
class DisasterMonitoringRequest(BaseModel):
    """災害監視開始リクエスト"""
    user_id: str = Field(..., description="ユーザーID")
    latitude: float = Field(..., description="緯度", ge=-90, le=90)
    longitude: float = Field(..., description="経度", ge=-180, le=180)
    radius_km: float = Field(default=50.0, description="監視範囲（km）", gt=0, le=200)

class DisasterMonitoringResponse(BaseModel):
    """災害監視開始レスポンス"""
    status: str = Field(..., description="ステータス（started/stopped/error）")
    message: str = Field(..., description="メッセージ")
    user_id: str = Field(..., description="ユーザーID")
    monitoring_area: Optional[Dict[str, Any]] = Field(None, description="監視エリア情報")

class DisasterAlert(BaseModel):
    """災害警報情報"""
    alert_id: str = Field(..., description="警報ID")
    alert_type: str = Field(..., description="警報種別")  # earthquake, tsunami, flood, weather, evacuation
    severity: str = Field(..., description="重要度")    # emergency, critical, warning, advisory
    title: str = Field(..., description="タイトル")
    content: str = Field(..., description="内容")
    source: str = Field(..., description="情報源")
    url: str = Field(..., description="詳細URL")
    timestamp: datetime = Field(..., description="発生時刻")
    affected_areas: List[str] = Field(default_factory=list, description="影響地域")
    coordinates: Optional[Dict[str, float]] = Field(None, description="座標情報")
    expiry_time: Optional[datetime] = Field(None, description="有効期限")
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式への変換（災害監視サービス互換）"""
        data = self.model_dump()
        data['timestamp'] = self.timestamp.isoformat()
        if self.expiry_time:
            data['expiry_time'] = self.expiry_time.isoformat()
        return data

class DisasterAlertsResponse(BaseModel):
    """災害警報一覧レスポンス"""
    user_id: str = Field(..., description="ユーザーID")
    alert_count: int = Field(..., description="警報数")
    alerts: List[DisasterAlert] = Field(..., description="災害警報一覧")
    last_updated: datetime = Field(..., description="最終更新時刻")

class AreaDisasterCheckRequest(BaseModel):
    """エリア災害情報チェックリクエスト"""
    latitude: float = Field(..., description="緯度", ge=-90, le=90)
    longitude: float = Field(..., description="経度", ge=-180, le=180)
    radius_km: float = Field(default=50.0, description="チェック範囲（km）", gt=0, le=200)

class AreaDisasterCheckResponse(BaseModel):
    """エリア災害情報チェックレスポンス"""
    location: Dict[str, float] = Field(..., description="チェック対象位置")
    alert_count: int = Field(..., description="発見された警報数")
    alerts: List[DisasterAlert] = Field(..., description="災害警報一覧")
    checked_at: datetime = Field(..., description="チェック実行時刻")
    sources_checked: List[str] = Field(..., description="チェックしたソース一覧")

class MonitoringStatus(BaseModel):
    """監視システムステータス"""
    is_running: bool = Field(..., description="監視システム稼働状態")
    monitored_users: int = Field(..., description="監視対象ユーザー数")
    active_alerts: int = Field(..., description="アクティブな警報数")
    check_interval_seconds: int = Field(..., description="チェック間隔（秒）")
    trusted_sources: List[str] = Field(..., description="信頼できるソース一覧")

class NewAlertsCheckResponse(BaseModel):
    """新規警報チェックレスポンス"""
    user_id: str = Field(..., description="ユーザーID")
    new_alert_count: int = Field(..., description="新規警報数")
    new_alerts: List[DisasterAlert] = Field(..., description="新規災害警報一覧")
    checked_at: datetime = Field(..., description="チェック実行時刻")
