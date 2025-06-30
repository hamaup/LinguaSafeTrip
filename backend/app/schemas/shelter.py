from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime

class ShelterStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    FULL = "full"
    UNKNOWN = "unknown"

class GeoPoint(BaseModel):
    latitude: float
    longitude: float

class ShelterInfo(BaseModel):
    id: str = Field(..., description="避難所ID")
    name: str = Field(..., description="避難所名称")
    latitude: float = Field(..., description="緯度")
    longitude: float = Field(..., description="経度")
    distance_km: float = Field(..., description="基準地点からの距離(km)")
    shelter_type: str = Field(..., description="避難所種別")
    status: ShelterStatus = Field(..., description="避難所ステータス")

class ShelterBase(BaseModel):
    name: str = Field(..., description="避難所名称")
    address: str = Field(..., description="住所")
    location: GeoPoint = Field(..., description="緯度経度")
    disaster_types: List[str] = Field(..., description="対応災害種別コードのリスト")
    capacity: Optional[int] = Field(None, description="収容人数")
    notes: Optional[str] = Field(None, description="備考")
    data_source: str = Field("GSI", description="データソース")
    # updated_at はFirestoreサーバータイムスタンプを使用することを想定し、
    # モデルには含めるが、クライアントからの入力は必須としないことが多い。
    # ここでは、読み取り時や内部処理用に定義しておく。
    updated_at: Optional[datetime] = Field(None, description="データ更新日時")

class ShelterCreate(ShelterBase):
    # 作成時は updated_at はサーバー側で設定するため、通常は不要
    pass

class ShelterUpdate(ShelterBase):
    # 更新時は一部フィールドのみ変更可能とする場合がある
    # ここでは簡単のため ShelterBase と同じとする
    name: Optional[str] = None
    address: Optional[str] = None
    location: Optional[GeoPoint] = None
    disaster_types: Optional[List[str]] = None
    capacity: Optional[int] = None
    notes: Optional[str] = None
    data_source: Optional[str] = None
    updated_at: Optional[datetime] = Field(None, description="データ更新日時、通常はサーバーで設定")


class ShelterInDB(ShelterBase):
    id: str = Field(..., description="FirestoreドキュメントID")
    # Firestoreから読み込む際に updated_at は datetime 型としてパースされる想定

    class Config:
        from_attributes = True # Pydantic V1, V2では from_attributes = True

# APIレスポンス用のモデル例
class ShelterResponse(ShelterInDB):
    distance_km: Optional[float] = Field(None, description="ユーザーからの距離 (km)")
    map_snapshot_url: Optional[str] = Field(None, description="地図スナップショットURL")

class ShelterNearbyRequest(BaseModel):
    latitude: float
    longitude: float
    radius_km: float = Field(default=3.0, gt=0, description="検索半径 (km)")
    current_disaster_type: Optional[str] = Field(None, description="現在発生している災害の種別")

class ShelterNearbyResponse(BaseModel):
    shelters: List[ShelterResponse]
