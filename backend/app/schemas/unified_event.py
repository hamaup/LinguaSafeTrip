from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from app.schemas.common.location import Location

class JMAFeedType(str, Enum):
    """気象庁のフィード種別を表すEnum"""
    EARTHQUAKE = "earthquake"
    TSUNAMI = "tsunami"
    WEATHER = "weather"
    VOLCANO = "volcano"
    OTHER = "other"

# LocationModel は廃止予定 - LocationInfoを使用してください
LocationModel = Location  # Backward compatibility alias

class ShelterInfo(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None # 開設状況 (例: "開設", "閉鎖", "準備中", "満員")
    capacity_status: Optional[str] = None # 混雑度 (例: "空きあり", "やや混雑", "満員")
    notes: Optional[str] = None

class FloodInfo(BaseModel):
    max_depth_meters: Optional[float] = None
    arrive_time_minutes: Optional[float] = None
    risk_level: Optional[str] = None # "氾濫危険", "避難判断", "注意", "浸水なし", "情報なし"

class UnifiedEventData(BaseModel):
    event_id: str = Field(..., description="システム内で一意なイベントID (例: jma_xxxx, lalert_yyyy)")
    event_type: str = Field(..., description="イベント種別 (例: earthquake, tsunami_warning, shelter_status_update)")
    source_name: str = Field(..., description="情報源名 (例: 気象庁XMLフィード, Lアラート, 全国避難所ガイドAPI)")
    original_id: Optional[str] = Field(None, description="情報源における元のID")

    headline: Optional[str] = Field(None, description="イベントの見出し")
    description: Optional[str] = Field(None, description="イベントの詳細説明")

    area_description: Optional[str] = Field(None, description="対象地域の説明文")
    area_codes: Optional[List[str]] = Field(None, description="関連する地域コード (例: JIS X 0402)")

    reported_at: datetime = Field(..., description="情報源での発表・更新日時 (UTC)")
    fetched_at: datetime = Field(..., description="システムが情報を取得した日時 (UTC)")

    severity: Optional[str] = Field(None, description="深刻度 (例: major, moderate, minor, info)")
    # JMAの電文では <jmx_eb:Severity> で表現されることがある (例: 警報級、注意報級)
    # Lアラートでは情報種別や本文から判断

    certainty: Optional[str] = Field(None, description="確度 (例: observed, likely, possible, unknown)")
    urgency: Optional[str] = Field(None, description="緊急度 (例: immediate, expected, future, past, unknown)")

    web_url: Optional[str] = Field(None, description="関連する情報源のURL")

    location: Optional[LocationModel] = Field(None, description="イベントに関連する位置情報 (震源地、避難所など)")

    # イベント種別ごとの詳細情報
    shelter_info: Optional[ShelterInfo] = Field(None, description="避難所関連情報")
    flood_info: Optional[FloodInfo] = Field(None, description="浸水関連情報")
    # earthquake_info: Optional[EarthquakeInfo] = None # 例
    # weather_alert_info: Optional[WeatherAlertInfo] = None # 例

    raw_data: Optional[Dict[str, Any]] = Field(None, description="正規化前の元データ (デバッグや詳細参照用)")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

# テスト用サンプルデータ
if __name__ == "__main__":
    sample_event = UnifiedEventData(
        event_id="jma_earthquake_20240101120000_123",
        event_type="earthquake",
        source_name="気象庁XMLフィード",
        original_id="urn:jma:jp:bosai:feed:20240101120000_0_VXSE5k_100000.xml",
        headline="石川県能登地方で震度7の地震発生",
        description="強い揺れに警戒してください。津波の可能性があります。",
        area_description="石川県能登地方",
        area_codes=["17201"], # 例: 輪島市
        reported_at=datetime.now(timezone.utc),
        fetched_at=datetime.now(timezone.utc),
        severity="major",
        certainty="observed",
        urgency="immediate",
        web_url="https://www.jma.go.jp/bosai/map.html#contents=earthquake_activity",
        location=LocationModel(latitude=37.5, longitude=137.0),
        raw_data={"original_xml_entry": "<entry>...</entry>"}
    )
    sample_shelter_event = UnifiedEventData(
        event_id="shelter_dynamic_hinanjyoguide_12345_20240101T150000Z",
        event_type="shelter_status_update",
        source_name="全国避難所ガイドAPI",
        original_id="12345",
        headline="〇〇避難所 開設 (空きあり)",
        reported_at=datetime.now(timezone.utc),
        fetched_at=datetime.now(timezone.utc),
        location=LocationModel(latitude=35.6, longitude=139.7),
        shelter_info=ShelterInfo(
            name="〇〇小学校 体育館",
            status="開設",
            capacity_status="空きあり"
        )
    )
