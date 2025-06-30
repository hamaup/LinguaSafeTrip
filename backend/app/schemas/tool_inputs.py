from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from ..schemas.contact import EmergencyContactSchema

class LocationInput(BaseModel):
    """地理的位置情報を表す入力モデル"""
    latitude: float = Field(...,
        description="Latitude of the location in decimal degrees.",
        ge=-90.0, le=90.0)
    longitude: float = Field(...,
        description="Longitude of the location in decimal degrees.",
        ge=-180.0, le=180.0)

class LocationBasedDisasterInfoInput(BaseModel):
    """災害情報検索ツールの入力モデル"""
    location: LocationInput = Field(...,
        description="The geographical location to search around.")
    radius_km: float = Field(
        default=50.0,
        ge=1.0, le=500.0,
        description="Search radius in kilometers (1-500km).")
    max_results_firestore: int = Field(
        default=5,
        ge=1, le=20,
        description="Maximum number of results to fetch from Firestore.")
    max_results_web: int = Field(
        default=3,
        ge=0, le=10,
        description="Maximum number of results to fetch from web search (0 to disable).")
    time_window_hours: int = Field(
        default=72,
        ge=1, le=168,
        description="How far back in hours to look for events (max 1 week).")
    search_web_if_no_firestore_results: bool = Field(
        default=True,
        description="Whether to perform web search if no results from Firestore.")
    web_search_query_override: Optional[str] = Field(
        default=None,
        description="Optional custom query to override default web search.")

class FcmAlertInfo(BaseModel):
    """FCMアラート情報のスキーマ"""
    id: str = Field(default="", description="アラートID")
    title: str = Field(..., description="通知のタイトル")
    body: str = Field(..., description="通知の本文")
    disaster_level: str = Field(default="warning", description="災害レベル")
    disaster_type: str = Field(default="emergency", description="災害タイプ")
    timestamp: str = Field(default="", description="タイムスタンプ")
    data: Optional[dict] = Field(
        default=None,
        description="追加のデータペイロード")


class GetInundationDepthToolInput(BaseModel):
    """浸水深度情報取得ツールの入力モデル"""
    location: LocationInput = Field(...,
        description="The geographical location to check inundation depth for.")
    radius_km: float = Field(
        default=5.0,
        ge=0.1, le=50.0,
        description="Search radius in kilometers (0.1-50km).")
    include_prediction: bool = Field(
        default=True,
        description="Whether to include predicted inundation depth.")
    include_historical: bool = Field(
        default=False,
        description="Whether to include historical inundation data.")
    source_preference: str = Field(
        default="auto",
        description="Preferred data source: 'auto', 'government', or 'sensor'")

class NearbyShelterSearchInput(BaseModel):
    """避難所検索の入力スキーマ"""
    latitude: float = Field(..., description="検索基準地点の緯度")
    longitude: float = Field(..., description="検索基準地点の経度")
    radius_km: float = Field(default=5.0, description="検索半径(km)")

class GuideSearchInput(BaseModel):
    """防災ガイド検索ツールの入力モデル"""
    query: str = Field(..., description="防災ガイドを検索するためのキーワードまたはトピック。")
    max_results: int = Field(default=3, description="返却するガイド結果の最大数。")

class WebSearchInput(BaseModel):
    """Web検索ツールの入力モデル"""
    query: str = Field(..., description="検索クエリ文字列。")
    num_results: int = Field(default=3, ge=1, le=10, description="返却する検索結果の数。")
    preferred_sites: Optional[List[str]] = Field(default=None, description="検索を優先または制限するドメインのリスト (例: ['go.jp', 'example.org'])。")
    required_keywords: Optional[List[str]] = Field(default=None, description="検索結果（タイトルまたはスニペット）に必須のキーワードのリスト。")
    summarize_content: bool = Field(default=False, description="上位の検索結果ページのコンテンツを取得し、要約するかどうか。")
    target_language: Optional[str] = Field(default="ja", description="検索APIがサポートしている場合、検索クエリと結果のターゲット言語。")

class ManageContactsInput(BaseModel):
    """緊急連絡先管理ツールの入力モデル"""
    action: Literal["add", "edit", "delete", "list", "request_info_for_add"] # 実行するアクション
    contact_data: Optional[EmergencyContactSchema] = Field(default=None, description="Contact data for add/edit actions.")
    contact_id_to_edit_or_delete: Optional[str] = Field(default=None, description="ID of the contact to edit or delete (managed by frontend).")

class TranslationToolInput(BaseModel):
    """翻訳ツールの入力モデル"""
    text: str = Field(..., description="翻訳するテキスト")
    target_language: str = Field(..., description="ターゲット言語コード (例: ja, en, ko)")
    source_language: Optional[str] = Field(default=None, description="ソース言語コード (自動検出の場合はNone)")

class TranslatedText(BaseModel):
    """翻訳結果のモデル"""
    original_text: str = Field(..., description="元のテキスト")
    translated_text: str = Field(..., description="翻訳されたテキスト")
    source_language: str = Field(..., description="検出されたソース言語")
    target_language: str = Field(..., description="ターゲット言語")
    confidence: Optional[float] = Field(default=None, description="翻訳の信頼度")
