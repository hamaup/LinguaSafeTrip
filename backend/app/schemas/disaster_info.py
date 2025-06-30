from datetime import datetime, timezone # timezoneをインポート
from enum import Enum
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
from app.schemas.common.enums import EmergencyLevel

# AlertLevel は廃止予定 - EmergencyLevelを使用してください
AlertLevel = EmergencyLevel  # Backward compatibility alias

class AreaCode(BaseModel):
    """地域コードを表すモデル"""
    name: str = Field(..., description="地域名")
    code: str = Field(pattern=r'^\d{6}$')  # 6桁の地域コード
    prefecture: Optional[str] = None

class RelevantDisasterEvent(BaseModel):
    """関連する災害イベント情報"""
    event_id: str = Field(..., description="イベントID")
    title: str = Field(..., description="イベントタイトル")
    event_type: str = Field(..., description="災害種別")
    severity: str = Field(..., description="深刻度レベル")
    timestamp: datetime = Field(..., description="データ取得時刻")
    event_time: datetime = Field(..., description="災害発生時刻")
    location: str = Field(..., description="発生場所")
    distance_km: float = Field(..., description="現在地からの距離(km)")
    alert_level: Optional[str] = Field(None, description="アラートレベル")
    description: str = Field(default="", description="災害の詳細説明")
    relevance_score: float = Field(default=0.0, description="ユーザー位置との関連性スコア(0-1)")

class JMAEventType(str, Enum):
    EARTHQUAKE = "earthquake_information"
    TSUNAMI = "tsunami_warning"
    WEATHER = "weather_alert"
    VOLCANO = "volcano_warning"
    OTHER = "other"

class JMAEventData(BaseModel):
    # JMAのAtomフィードIDは urn:jma:jp:bosai:feed:YYYYMMDDhhmmss_X_XXXXXX_XXXXXX.xml の形式
    # normalize_jma_xml_entry_to_dict で "jma_" プレフィックスが付加される
    event_id: str = Field(..., pattern=r'^(jma_)?.*$')  # パターンを緩和
    title: str
    published_at: datetime
    updated_at: Optional[datetime] = None  # Optional化
    author_name: Optional[str] = None
    event_type: Optional[JMAEventType] = None  # Optional化
    areas: Optional[List[AreaCode]] = None  # Optional化
    content: Optional[str] = None
    xml_link: Optional[str] = None
    related_links: Optional[List[Dict[str, str]]] = None
    raw_feed_entry: Optional[Dict[str, Any]] = None
    alert_level: Optional[AlertLevel] = None
    magnitude: Optional[float] = Field(None, ge=0, le=10)
    
    # JMAXMLの三層構造対応フィールド
    info_kind: Optional[str] = None
    serial: Optional[str] = None
    info_type: Optional[str] = None
    severity: Optional[str] = None
    area_name: Optional[str] = None
    target_date_time: Optional[str] = None
    report_date_time: Optional[str] = None
    editorial_office: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

    @field_validator('published_at', 'updated_at', mode='before')
    def parse_jst_time(cls, v):
        if isinstance(v, str):
            # JSTタイムゾーンを考慮してパース
            return datetime.strptime(v, "%Y-%m-%dT%H:%M:%S%z").astimezone(timezone.utc)
        elif isinstance(v, datetime) and v.tzinfo is None:
            # タイムゾーン情報がない場合はUTCとして扱う
            return v.replace(tzinfo=timezone.utc)
        return v

class JMAFeedResponse(BaseModel):
    feed_url: str
    entries: List[JMAEventData]
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class JMAFeedType(str, Enum):
    """気象庁フィードの種類を表す列挙型"""
    REGULAR = "REGULAR"  # 通常フィード
    EXTRA = "EXTRA"      # 速報フィード
    VOLCANO = "VOLCANO"  # 火山関連フィード
    QUAKE = "QUAKE"      # 地震関連フィード


class InundationDepthResult(BaseModel):
    """浸水深度情報の結果モデル"""
    depth_value: float = Field(..., ge=0, description="浸水深度の値")
    depth_unit: str = Field(default="m", description="深度の単位 (m/cm)")
    source: str = Field(..., description="データソース (政府/センサー/予測)")
    is_prediction: bool = Field(..., description="予測データかどうか")
    timestamp: datetime = Field(..., description="データ取得時刻")
    location: Optional[AreaCode] = Field(None, description="対象地域情報")
    confidence: Optional[float] = Field(
        None, ge=0, le=1,
        description="データ信頼度 (0-1)")
    additional_info: Optional[Dict[str, Any]] = Field(
        None, description="追加情報")


class DisasterContext(BaseModel):
    """災害コンテキストスキーマ"""
    disaster_type: str = Field(..., description="災害種別")
    severity: Literal["low", "medium", "high", "extreme"] = Field(..., description="深刻度レベル")
    affected_areas: List[str] = Field(default_factory=list, description="影響地域リスト")
    last_updated: datetime = Field(..., description="最終更新時刻")
