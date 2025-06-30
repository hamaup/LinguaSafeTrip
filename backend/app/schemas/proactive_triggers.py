from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime

class TriggerContext(BaseModel):
    trigger_type: Literal[
        "new_disaster_alert_jma", # 新しいJMA災害警報
        "significant_weather_change", # 天候の著しい変化 (将来用)
        "user_viewed_specific_guide", # 特定の防災ガイド閲覧
        "emergency_contact_not_set_up", # 緊急連絡先未設定 (オンボーディング後など)
        "long_time_no_see_user", # 長期間未利用ユーザー
        "approaching_disaster_anniversary", # 災害記念日の接近 (将来用)
        "after_safety_check_in", # 安否確認後
        "location_in_hazard_area" # 現在地がハザードエリア内 (ハザードマップ連携後)
    ]
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    related_data: Optional[Dict[str, Any]] = None # トリガーに関連するデータ
    urgency_score: Optional[int] = Field(default=1, ge=0, le=10) # 提案の緊急度 (0-10)
    relevance_score: Optional[float] = Field(default=0.5, ge=0.0, le=1.0) # ユーザーへの関連度
