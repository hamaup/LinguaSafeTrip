# backend/app/schemas/hazard.py
"""
ハザードマップ関連のスキーマ定義
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Tuple, Any
from datetime import datetime
from enum import Enum

from app.schemas.common.location import Location


class HazardType(str, Enum):
    """ハザード種別"""
    TSUNAMI = "tsunami"  # 津波
    FLOOD = "flood"  # 洪水
    LANDSLIDE = "landslide"  # 土砂災害
    HIGH_TIDE = "high_tide"  # 高潮
    INTERNAL_FLOOD = "internal_flood"  # 内水氾濫
    AVALANCHE = "avalanche"  # 雪崩


class HazardLevel(str, Enum):
    """危険度レベル"""
    NONE = "none"  # 危険なし
    LOW = "low"  # 低
    MEDIUM = "medium"  # 中
    HIGH = "high"  # 高
    EXTREME = "extreme"  # 極めて高い


class HazardDetail(BaseModel):
    """個別ハザード詳細"""
    hazard_type: HazardType = Field(..., description="ハザード種別")
    level: HazardLevel = Field(..., description="危険度レベル")
    depth: Optional[float] = Field(None, description="浸水深（メートル）")
    probability: Optional[float] = Field(None, description="発生確率（0-1）")
    description: str = Field(..., description="説明文")
    source: str = Field(..., description="データソース")
    updated_at: datetime = Field(..., description="データ更新日時")


class TileCoordinates(BaseModel):
    """タイル座標情報"""
    zoom: int = Field(..., ge=2, le=17, description="ズームレベル")
    x: int = Field(..., description="X座標")
    y: int = Field(..., description="Y座標")


class HazardInfo(BaseModel):
    """統合ハザード情報"""
    location: Location = Field(..., description="対象位置")
    hazards: List[HazardDetail] = Field(..., description="ハザード詳細リスト")
    overall_risk_level: HazardLevel = Field(..., description="総合危険度")
    tile_coordinates: Dict[str, Any] = Field(..., description="使用タイル座標")
    analyzed_at: datetime = Field(..., description="解析日時")
    cache_key: str = Field(..., description="キャッシュキー")


class Shelter(BaseModel):
    """基本避難所情報"""
    id: str = Field(..., description="避難所ID")
    name: str = Field(..., description="避難所名")
    location: Location = Field(..., description="位置情報")
    capacity: int = Field(..., ge=0, description="収容人数")
    shelter_type: Optional[str] = Field(None, description="避難所タイプ")
    facilities: Optional[List[str]] = Field(None, description="利用可能設備")
    
    
class SafeShelter(BaseModel):
    """安全性評価済み避難所"""
    id: str = Field(..., description="避難所ID")
    name: str = Field(..., description="避難所名")
    location: Location = Field(..., description="位置情報")
    elevation: float = Field(..., description="標高（メートル）")
    building_floors: Optional[int] = Field(None, ge=1, description="建物階数")
    capacity: int = Field(..., ge=0, description="収容人数")
    distance: float = Field(..., ge=0, description="現在地からの距離（km）")
    estimated_time: int = Field(..., ge=0, description="到達予想時間（分）")
    is_tsunami_safe: bool = Field(..., description="津波対応可否")
    is_safe: bool = Field(..., description="総合安全判定")
    safety_score: float = Field(..., ge=0, le=1, description="安全スコア（0-1）")
    hazard_info: Optional[Dict[str, Any]] = Field(None, description="ハザード情報サマリー")


class TsunamiShelter(BaseModel):
    """津波対応避難所"""
    id: str = Field(..., description="避難所ID")
    name: str = Field(..., description="避難所名")
    location: Location = Field(..., description="位置情報")
    elevation: float = Field(..., description="標高（メートル）")
    building_floors: Optional[int] = Field(None, ge=1, description="建物階数")
    capacity: int = Field(..., ge=0, description="収容人数")
    distance: float = Field(..., ge=0, description="現在地からの距離（km）")
    estimated_time: int = Field(..., ge=0, description="到達予想時間（分）")
    is_tsunami_safe: bool = Field(..., description="津波対応可否")
    safety_score: float = Field(..., ge=0, le=1, description="安全スコア（0-1）")


class TsunamiEvacuationPlan(BaseModel):
    """津波避難計画"""
    current_risk: Optional[HazardDetail] = Field(None, description="現在地の津波リスク")
    recommended_shelters: List[TsunamiShelter] = Field(..., description="推奨避難所リスト")
    evacuation_required: bool = Field(..., description="避難必要性")
    time_to_impact: Optional[int] = Field(None, description="津波到達予想時間（分）")
    recommended_action: str = Field(..., description="推奨行動")


# API Request/Response Models

class HazardRequest(BaseModel):
    """ハザード情報リクエスト"""
    location: Location = Field(..., description="確認位置")
    hazard_types: Optional[List[HazardType]] = Field(None, description="取得するハザード種別")
    zoom_level: int = Field(16, ge=2, le=17, description="ズームレベル")


class HazardResponse(BaseModel):
    """ハザード情報レスポンス"""
    success: bool = Field(..., description="成功フラグ")
    data: Optional[HazardInfo] = Field(None, description="ハザード情報")
    error: Optional[str] = Field(None, description="エラーメッセージ")


class TsunamiEvacuationRequest(BaseModel):
    """津波避難計画リクエスト"""
    location: Location = Field(..., description="現在位置")
    max_distance_km: float = Field(5.0, gt=0, le=20, description="検索範囲（km）")
    max_shelters: int = Field(5, ge=1, le=10, description="最大避難所数")


class TsunamiEvacuationResponse(BaseModel):
    """津波避難計画レスポンス"""
    success: bool = Field(..., description="成功フラグ")
    data: Optional[TsunamiEvacuationPlan] = Field(None, description="避難計画")
    error: Optional[str] = Field(None, description="エラーメッセージ")


class RoutePoint(BaseModel):
    """経路上の地点"""
    location: Location = Field(..., description="位置")
    distance_from_start: float = Field(..., ge=0, description="開始地点からの距離（km）")


class RouteSafetyCheck(BaseModel):
    """経路安全性チェック結果"""
    route_points: List[RoutePoint] = Field(..., description="チェック地点リスト")
    hazards_on_route: List[HazardDetail] = Field(..., description="経路上のハザード")
    is_safe: bool = Field(..., description="安全判定")
    warnings: List[str] = Field(..., description="警告メッセージ")
    alternative_suggested: bool = Field(..., description="代替経路推奨")


class RouteSafetyRequest(BaseModel):
    """経路安全性チェックリクエスト"""
    origin: Location = Field(..., description="出発地")
    destination: Location = Field(..., description="目的地")
    check_interval_km: float = Field(0.5, gt=0, le=2, description="チェック間隔（km）")


class RouteSafetyResponse(BaseModel):
    """経路安全性チェックレスポンス"""
    success: bool = Field(..., description="成功フラグ")
    data: Optional[RouteSafetyCheck] = Field(None, description="チェック結果")
    error: Optional[str] = Field(None, description="エラーメッセージ")